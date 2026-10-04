from ultralytics import YOLO

from config import YOLO_MODEL_PATH, CONFIDENCE_THRESHOLD


class PersonDetector:

    def __init__(self):

        print("Loading YOLO11n person detection model...")

        self.model = YOLO(
            str(YOLO_MODEL_PATH)
        )

        print("YOLO11n model loaded.")


    def detect(self, frame):

        results = self.model.predict(
            source=frame,
            conf=CONFIDENCE_THRESHOLD,
            classes=[0],
            imgsz=640,
            verbose=False
        )

        detections = []

        result = results[0]

        for box in result.boxes:

            confidence = float(box.conf[0])

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            detections.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": confidence
            })

        return detections