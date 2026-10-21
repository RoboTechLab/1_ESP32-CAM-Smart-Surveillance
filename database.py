import sqlite3

from config import DATABASE_PATH


def get_connection():

    return sqlite3.connect(DATABASE_PATH)


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (

            event_id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,

            object_type TEXT NOT NULL,

            confidence REAL NOT NULL,

            image_path TEXT NOT NULL
        )
        """
    )

    # RCWL trigger batches stored separately from camera snapshots.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motion_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            trigger_count INTEGER NOT NULL CHECK(trigger_count > 0)
        )
    """)

    connection.commit()

    connection.close()

    print("Database initialized.")


def insert_event(timestamp, object_type, confidence, image_path):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO events
        (
            timestamp,
            object_type,
            confidence,
            image_path
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            timestamp,
            object_type,
            confidence,
            image_path
        )
    )

    connection.commit()

    event_id = cursor.lastrowid

    connection.close()

    return event_id

def get_recent_events(limit=10):

    connection = get_connection()

    # Allows accessing columns by name
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            event_id,
            timestamp,
            object_type,
            confidence,
            image_path
        FROM events
        ORDER BY event_id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    events = []

    for row in rows:

        events.append({
            "event_id": row["event_id"],
            "timestamp": row["timestamp"],
            "object_type": row["object_type"],
            "confidence": row["confidence"],
            "image_path": row["image_path"]
        })

    return events


def get_event_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM events"
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count

def get_dashboard_statistics():

    connection = get_connection()
    cursor = connection.cursor()

    # ----------------------------------
    # TOTAL EVENTS
    # ----------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM events
        """
    )

    total_events = cursor.fetchone()[0]

    # ----------------------------------
    # TODAY'S EVENTS
    # ----------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM events
        WHERE DATE(timestamp) = DATE('now', 'localtime')
        """
    )

    today_events = cursor.fetchone()[0]

    # ----------------------------------
    # LAST DETECTION
    # ----------------------------------

    cursor.execute(
        """
        SELECT timestamp
        FROM events
        ORDER BY event_id DESC
        LIMIT 1
        """
    )

    result = cursor.fetchone()

    if result:
        last_detection = result[0]
    else:
        last_detection = None

    cursor.execute("SELECT COALESCE(SUM(trigger_count), 0) FROM motion_events")
    motion_total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(trigger_count), 0)
        FROM motion_events
        WHERE DATE(timestamp) = DATE('now', 'localtime')
    """)
    motion_today = cursor.fetchone()[0]

    connection.close()

    # Descriptive ratio only: different detection systems may count
    # different kinds of events; do not call this camera accuracy.
    today_ratio = round(today_events / motion_today * 100, 1) if motion_today else None
    today_difference = motion_today - today_events

    return {
        "motion_total": motion_total,
        "motion_today": motion_today,
        "today_camera_to_motion_ratio": today_ratio,
        "today_event_difference": today_difference,
        "total_events": total_events,
        "today_events": today_events,
        "last_detection": last_detection
    }

def insert_motion_batch(timestamp, trigger_count):
    """Save newly observed RCWL rising edges, grouped at observation time."""
    if not isinstance(trigger_count, int) or trigger_count <= 0:
        return
    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO motion_events (timestamp, trigger_count) VALUES (?, ?)",
            (timestamp, trigger_count)
        )
        connection.commit()
    finally:
        connection.close()
