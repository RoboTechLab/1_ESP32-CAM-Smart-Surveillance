import cv2
import threading
import time
from datetime import datetime

from config import EVENTS_DIR
from database import insert_event
from telegram_bot import send_person_alert


class EventManager:

    def __init__(self):

        EVENTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # Is there already an active person-presence event?
        self.person_event_active = False

        # Are we currently collecting candidate frames?
        self.collecting_best_frame = False

        # Best candidate information
        self.best_frame = None
        self.best_confidence = 0.0
        self.best_score = 0.0

        # Collect candidate frames for this long
        self.capture_window = 1.0

        # Protect shared data between threads
        self.lock = threading.Lock()


    def person_detected(
        self,
        frame,
        confidence,
        box_area_ratio
    ):

        # ----------------------------------
        # NEW PERSON EVENT
        # ----------------------------------

        if not self.person_event_active:

            self.person_event_active = True
            self.collecting_best_frame = True

            print()
            print("Person detected.")
            print(
                "Collecting best snapshot "
                "for 1 second..."
            )

            # Start with the first detected frame
            self._update_best_frame(
                frame,
                confidence,
                box_area_ratio
            )

            # Start timer in background
            worker = threading.Thread(
                target=self._finish_capture_after_delay,
                daemon=True
            )

            worker.start()

            return

        # ----------------------------------
        # PERSON STILL PRESENT
        # ----------------------------------

        # During the first second, continue looking
        # for a better snapshot.
        if self.collecting_best_frame:

            self._update_best_frame(
                frame,
                confidence,
                box_area_ratio
            )


    def _update_best_frame(
        self,
        frame,
        confidence,
        box_area_ratio
    ):

        # ----------------------------------
        # SNAPSHOT QUALITY SCORE
        # ----------------------------------
        #
        # Confidence tells us how certain YOLO is.
        # Box area tells us how much of the image
        # the detected person occupies.
        #
        # Give more importance to person size.

        score = (
            0.4 * confidence
            + 0.6 * box_area_ratio
        )

        with self.lock:

            if score > self.best_score:

                self.best_score = score
                self.best_confidence = confidence

                # IMPORTANT:
                # Keep our own copy of this frame.
                self.best_frame = frame.copy()


    def _finish_capture_after_delay(self):

        # Allow the person time to enter the view
        time.sleep(self.capture_window)

        with self.lock:

            self.collecting_best_frame = False

            if self.best_frame is None:
                return

            frame = self.best_frame.copy()
            confidence = self.best_confidence

            # Clear candidate memory
            self.best_frame = None
            self.best_confidence = 0.0
            self.best_score = 0.0

        # Event processing happens in this background
        # thread, so Telegram cannot freeze the camera.
        self._process_event(
            frame,
            confidence
        )


    def _process_event(
        self,
        frame,
        confidence
    ):

        now = datetime.now()

        timestamp = now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        filename = now.strftime(
            "person_%Y%m%d_%H%M%S.jpg"
        )

        image_path = (
            EVENTS_DIR / filename
        )

        # ----------------------------------
        # SAVE BEST SNAPSHOT
        # ----------------------------------

        success = cv2.imwrite(
            str(image_path),
            frame
        )

        if not success:

            print(
                "ERROR: Snapshot could not "
                "be saved."
            )

            return

        # ----------------------------------
        # DATABASE
        # ----------------------------------

        event_id = insert_event(
            timestamp=timestamp,
            object_type="Person",
            confidence=confidence,
            image_path=str(image_path)
        )

        print()
        print("============================")
        print("NEW PERSON EVENT")
        print("============================")
        print(f"Event ID   : {event_id}")
        print(f"Time       : {timestamp}")
        print(
            f"Confidence : "
            f"{confidence * 100:.1f}%"
        )
        print(f"Snapshot   : {image_path}")
        print("============================")
        print()

        # ----------------------------------
        # TELEGRAM
        # ----------------------------------

        telegram_success = send_person_alert(
            image_path=str(image_path),
            timestamp=timestamp,
            confidence=confidence
        )

        print(
            f"Telegram for event "
            f"{event_id}: "
            f"{'SENT' if telegram_success else 'FAILED'}"
        )


    def person_left(self):

        if self.person_event_active:

            self.person_event_active = False

            print()
            print("Person left camera view.")
            print("Surveillance system rearmed.")
            print()

    def additional_person_detected(
        self,
        frame,
        confidence,
        person_count
    ):

        print()
        print(
            f"Additional person detected. "
            f"Current people: {person_count}"
        )

        event_frame = frame.copy()
   
        worker = threading.Thread(
            target=self._process_additional_person_event,
            args=(
                event_frame,
                confidence,
                person_count
            ),
            daemon=True
        )

        worker.start()

    def _process_additional_person_event(
        self,
        frame,
        confidence,
        person_count
    ):

        now = datetime.now()

        timestamp = now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        filename = now.strftime(
            "person_%Y%m%d_%H%M%S.jpg"
        )

        image_path = EVENTS_DIR / filename

        success = cv2.imwrite(
            str(image_path),
            frame
        )

        if not success:
            print(
                "ERROR: Additional-person "
                "snapshot could not be saved."
            )
            return

        event_id = insert_event(
            timestamp=timestamp,
            object_type="Person",
            confidence=confidence,
            image_path=str(image_path)
        )

        print()
        print("============================")
        print("ADDITIONAL PERSON EVENT")
        print("============================")
        print(f"Event ID     : {event_id}")
        print(f"People       : {person_count}")
        print(f"Time         : {timestamp}")
        print(
            f"Confidence   : "
            f"{confidence * 100:.1f}%"
        )
        print("============================")
        print()

        telegram_success = send_person_alert(
            image_path=str(image_path),
            timestamp=timestamp,
            confidence=confidence
        )

        print(
            f"Telegram for event {event_id}: "
            f"{'SENT' if telegram_success else 'FAILED'}"
        )
    