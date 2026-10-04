import cv2
import threading
import time

from config import CAMERA_SOURCE
from detector import PersonDetector
from event_manager import EventManager


class CameraService:

    def __init__(self):

        self.camera = cv2.VideoCapture(CAMERA_SOURCE)

        if not self.camera.isOpened():
            raise RuntimeError("Could not open camera.")

        self.detector = PersonDetector()
        self.event_manager = EventManager()

        # ----------------------------------
        # DASHBOARD / CAMERA STATE
        # ----------------------------------

        self.latest_frame = None

        self.camera_online = True
        self.person_detected = False
        self.confidence = 0.0

        self.running = True

        # ----------------------------------
        # PERSON LEAVE / REARM STATE
        # ----------------------------------

        self.last_person_seen = None

        # Person must be absent for 2 seconds
        # before the system rearms.
        self.person_leave_delay = 2.0

        # ----------------------------------
        # PERSON COUNT STATE
        # ----------------------------------

        self.previous_person_count = 0

        # Used to confirm that a new person
        # really entered the scene.
        self.pending_person_count = 0
        self.pending_count_frames = 0

        # New count must remain for 3 frames
        # before we accept it.
        self.count_confirmation_frames = 3

        # ----------------------------------
        # START CAMERA THREAD
        # ----------------------------------

        # IMPORTANT:
        # Start the thread only AFTER all
        # variables above have been created.

        self.thread = threading.Thread(
            target=self._process_camera,
            daemon=True
        )

        self.thread.start()

        print("Camera service started.")


    def _process_camera(self):

        while self.running:

            # ----------------------------------
            # READ CAMERA
            # ----------------------------------

            ret, frame = self.camera.read()

            if not ret:

                self.camera_online = False
                time.sleep(0.05)

                continue

            self.camera_online = True

            # ----------------------------------
            # YOLO PERSON DETECTION
            # ----------------------------------

            detections = self.detector.detect(frame)

            current_person_count = len(detections)

            current_time = time.time()

            # ----------------------------------
            # CURRENT DETECTION STATUS
            # ----------------------------------

            if detections:

                self.person_detected = True

                best_detection = max(
                    detections,
                    key=lambda d: d["confidence"]
                )

                self.confidence = (
                    best_detection["confidence"]
                )

                # At least one person was seen now.
                self.last_person_seen = current_time

            else:

                self.person_detected = False
                self.confidence = 0.0

                best_detection = None

            # ----------------------------------
            # PERSON COUNT INCREASE
            #
            # Examples:
            #
            # 0 -> 1
            # 1 -> 2
            # 2 -> 3
            # ----------------------------------

            if (
                current_person_count
                > self.previous_person_count
            ):

                if (
                    current_person_count
                    == self.pending_person_count
                ):

                    self.pending_count_frames += 1

                else:

                    self.pending_person_count = (
                        current_person_count
                    )

                    self.pending_count_frames = 1

                # Confirm the increase only after
                # seeing it for several frames.
                if (
                    self.pending_count_frames
                    >= self.count_confirmation_frames
                ):

                    old_count = (
                        self.previous_person_count
                    )

                    self.previous_person_count = (
                        current_person_count
                    )

                    self.pending_person_count = 0
                    self.pending_count_frames = 0

                    print(
                        f"Person count increased: "
                        f"{old_count} -> "
                        f"{current_person_count}"
                    )

                    # ----------------------------------
                    # ADDITIONAL PERSON
                    #
                    # 1 -> 2
                    # 2 -> 3
                    # etc.
                    # ----------------------------------

                    if (
                        old_count > 0
                        and best_detection is not None
                    ):

                        self.event_manager.additional_person_detected(
                            frame,
                            best_detection["confidence"],
                            current_person_count
                        )

            else:

                self.pending_person_count = 0
                self.pending_count_frames = 0

            # ----------------------------------
            # PERSON COUNT DECREASE
            #
            # Examples:
            #
            # 3 -> 2
            # 2 -> 1
            #
            # Do NOT send Telegram alert.
            # ----------------------------------

            if (
                current_person_count > 0
                and
                current_person_count
                < self.previous_person_count
            ):

                print(
                    f"Person count decreased: "
                    f"{self.previous_person_count} "
                    f"-> {current_person_count}"
                )

                self.previous_person_count = (
                    current_person_count
                )

            # ----------------------------------
            # DRAW YOLO BOXES
            # ----------------------------------

            for detection in detections:

                x1 = detection["x1"]
                y1 = detection["y1"]
                x2 = detection["x2"]
                y2 = detection["y2"]

                confidence = (
                    detection["confidence"]
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                label = (
                    f"PERSON "
                    f"{confidence * 100:.1f}%"
                )

                cv2.putText(
                    frame,
                    label,
                    (
                        x1,
                        max(y1 - 10, 20)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            # ----------------------------------
            # NORMAL PERSON EVENT
            #
            # This keeps our existing
            # 1-second best-frame system.
            # ----------------------------------

            if (
                detections
                and best_detection is not None
            ):

                frame_height, frame_width = (
                    frame.shape[:2]
                )

                box_width = max(
                    0,
                    best_detection["x2"]
                    - best_detection["x1"]
                )

                box_height = max(
                    0,
                    best_detection["y2"]
                    - best_detection["y1"]
                )

                box_area = (
                    box_width
                    * box_height
                )

                frame_area = (
                    frame_width
                    * frame_height
                )

                if frame_area > 0:

                    box_area_ratio = (
                        box_area
                        / frame_area
                    )

                else:

                    box_area_ratio = 0.0

                self.event_manager.person_detected(
                    frame,
                    best_detection["confidence"],
                    box_area_ratio
                )

            # ----------------------------------
            # NO PERSON
            #
            # Wait 2 seconds before rearming.
            # ----------------------------------

            else:

                if self.last_person_seen is not None:

                    absence_time = (
                        current_time
                        - self.last_person_seen
                    )

                    if (
                        absence_time
                        >= self.person_leave_delay
                    ):

                        self.event_manager.person_left()

                        print(
                            "Person count reset: "
                            f"{self.previous_person_count} -> 0"
                        )

                        self.previous_person_count = 0

                        self.pending_person_count = 0
                        self.pending_count_frames = 0

                        self.last_person_seen = None

            # ----------------------------------
            # DASHBOARD VIDEO FRAME
            #
            # IMPORTANT:
            # This must run EVERY camera loop.
            # ----------------------------------

            success, buffer = cv2.imencode(
                ".jpg",
                frame
            )

            if success:

                self.latest_frame = (
                    buffer.tobytes()
                )


    def get_frame(self):

        return self.latest_frame


    def get_status(self):

        return {

            "camera_online":
                self.camera_online,

            "person_detected":
                self.person_detected,

            "confidence":
                self.confidence
        }


    def stop(self):

        self.running = False

        self.camera.release()