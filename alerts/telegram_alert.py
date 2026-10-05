import random

import requests


class TelegramAlert:

    def __init__(self, bot_token, chat_id):
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.alert_attempted = False

    @classmethod
    def from_config(cls, bot_token, chat_id):
        if not bot_token or not chat_id:
            print(
                "[INFO] Telegram alerts disabled: configure "
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
            )
            return None

        return cls(bot_token, chat_id)

    def send(self, event, track_id, confidence, frame_number):
        if self.alert_attempted:
            return False

        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)
        message = (
            "Anomaly detected\n"
            f"Event: {event}\n"
            f"Track: {track_id}\n"
            f"Confidence: {confidence:.0%}\n"
            f"Frame: {frame_number}\n"
            f"Location: {latitude:.6f}, {longitude:.6f}\n"
            f"Map: https://maps.google.com/?q={latitude:.6f},{longitude:.6f}"
        )

        try:
            response = requests.post(
                self.url,
                data={"chat_id": self.chat_id, "text": message},
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()
            if not result.get("ok"):
                raise RuntimeError(
                    result.get("description", "Telegram API request failed")
                )

            self.alert_attempted = True
            print("[INFO] Telegram alert sent.")
            return True
        except (requests.RequestException, ValueError, RuntimeError) as error:
            print(f"[ERROR] Could not send Telegram alert: {error}")
            return False
