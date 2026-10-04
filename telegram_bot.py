import os
import requests
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def telegram_configured():
    return bool(BOT_TOKEN and CHAT_ID)


def send_person_alert(
    image_path,
    timestamp,
    confidence
):

    if not telegram_configured():

        print(
            "WARNING: Telegram is not configured."
        )

        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendPhoto"
    )

    caption = (
        "🚨 PERSON DETECTED\n\n"
        f"Time: {timestamp}\n"
        f"Confidence: "
        f"{confidence * 100:.1f}%\n"
        "Location: Laboratory Surveillance Zone"
    )

    try:

        with open(image_path, "rb") as image_file:

            response = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "caption": caption
                },
                files={
                    "photo": image_file
                },
                timeout=15
            )

        response.raise_for_status()

        result = response.json()

        if result.get("ok"):

            print(
                "Telegram notification sent."
            )

            return True

        print(
            "ERROR: Telegram rejected notification."
        )

        return False

    except FileNotFoundError:

        print(
            f"ERROR: Snapshot not found: "
            f"{image_path}"
        )

        return False

    except requests.RequestException as error:

        print(
            f"ERROR sending Telegram alert: "
            f"{error}"
        )

        return False