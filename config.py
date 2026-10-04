from pathlib import Path

# -------------------------------------------------
# PROJECT PATHS
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

YOLO_MODEL_PATH = BASE_DIR / "yolo11n.pt"

EVENTS_DIR = BASE_DIR / "events"

DATABASE_PATH = BASE_DIR / "surveillance.db"


# -------------------------------------------------
# AI SETTINGS
# -------------------------------------------------

CONFIDENCE_THRESHOLD = 0.60

NMS_THRESHOLD = 0.30

TOP_K = 5000


# -------------------------------------------------
# EVENT SETTINGS
# -------------------------------------------------

# Prevent repeated events while the same person
# remains in front of the camera.
EVENT_COOLDOWN_SECONDS = 15


# -------------------------------------------------
# CAMERA SETTINGS
# -------------------------------------------------

# 0 = laptop's default webcam.
# Later this will be replaced by the ESP32-CAM URL.
CAMERA_SOURCE = 0