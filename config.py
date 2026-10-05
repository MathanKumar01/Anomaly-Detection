import os

from dotenv import load_dotenv

load_dotenv()

# Telegram settings. Keep credentials in environment variables.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Default video path - points to existing sample in dataset
VIDEO_PATH = os.path.join("dataset", "Assault011_x264.mp4")

# YOLO Models
YOLO_MODEL = "yolo11n.pt"
POSE_MODEL = "yolo11n-pose.pt"

# Settings
CONFIDENCE = 0.5
ENABLE_POSE = True
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720