from flask import (
    Flask,
    render_template,
    Response,
    jsonify,
    send_from_directory
)

from database import (
    initialize_database,
    get_recent_events,
    get_event_count,
    get_dashboard_statistics
)
from camera_service import CameraService
from config import EVENTS_DIR
import time


app = Flask(__name__)


print("------------------------------------")
print("RoboTech Smart Surveillance Server")
print("------------------------------------")


initialize_database()

camera_service = CameraService()


@app.route("/")
def index():

    return render_template(
        "index.html"
    )


@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype=(
            "multipart/x-mixed-replace;"
            " boundary=frame"
        )
    )


def generate_frames():

    while True:

        frame = camera_service.get_frame()

        if frame is None:
            time.sleep(0.01)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: " +
            str(len(frame)).encode() +
            b"\r\n\r\n" +
            frame +
            b"\r\n"
        )

        time.sleep(0.03)


@app.route("/status")
def status():

    return jsonify(
        camera_service.get_status()
    )

@app.route("/events")
def events():

    recent_events = get_recent_events(
        limit=10
    )

    total_events = get_event_count()

    # Remove the local Windows path from what
    # gets sent to the browser.
    for event in recent_events:

        event["image_url"] = (
            f"/event_image/"
            f"{event['event_id']}"
        )

        event.pop(
            "image_path",
            None
        )

    return jsonify({
        "total_events": total_events,
        "events": recent_events
    })


@app.route("/event_image/<int:event_id>")
def event_image(event_id):

    events = get_recent_events(
        limit=1000
    )

    for event in events:

        if event["event_id"] == event_id:

            image_path = event["image_path"]

            from pathlib import Path

            filename = Path(
                image_path
            ).name

            return send_from_directory(
                EVENTS_DIR,
                filename
            )

    return "Image not found", 404

@app.route("/statistics")
def statistics():

    stats = get_dashboard_statistics()

    return jsonify(stats)


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )