import os
import cv2
import numpy as np
import requests
from gtts import gTTS
from datetime import datetime
import subprocess
import importlib.metadata

# -----------------------------
# Dependency Check
# -----------------------------
print("Checking dependencies...")
print(f"✅ OpenCV version: {cv2.__version__}")
print(f"✅ NumPy version: {np.__version__}")

try:
    gtts_version = importlib.metadata.version("gTTS")
    print(f"✅ gTTS version: {gtts_version}")
except importlib.metadata.PackageNotFoundError:
    print("❌ gTTS package not found. Please install it.")
    raise SystemExit(1)

try:
    subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    print("✅ FFmpeg is installed")
except Exception:
    print("❌ FFmpeg not found. Please install FFmpeg.")
    raise SystemExit(1)

# -----------------------------
# Telegram Config
# -----------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Telegram credentials missing in environment variables.")
    raise SystemExit(1)

# -----------------------------
# AI News Content
# -----------------------------
news_text = """
AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch.
"""

# -----------------------------
# Convert Text to Speech
# -----------------------------
tts = gTTS(text=news_text, lang="en")
audio_file = "news.mp3"
tts.save(audio_file)

# -----------------------------
# Create Video Frames using OpenCV
# -----------------------------
width, height = 1280, 720
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1
font_color = (255, 255, 255)
line_type = 2
duration_sec = 15
fps = 24
total_frames = duration_sec * fps

# Split text into lines
lines = news_text.strip().split("\n")
line_y = height // 2 - (len(lines) * 30)

video_file = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_writer = cv2.VideoWriter("temp_video.mp4", fourcc, fps, (width, height))

for _ in range(total_frames):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    y = line_y
    for line in lines:
        text_size = cv2.getTextSize(line, font, font_scale, line_type)[0]
        x = (width - text_size[0]) // 2
        cv2.putText(frame, line, (x, y), font, font_scale, font_color, line_type, cv2.LINE_AA)
        y += 50
    video_writer.write(frame)

video_writer.release()

# -----------------------------
# Combine video and audio using FFmpeg
# -----------------------------
ffmpeg_command = [
    "ffmpeg",
    "-y",
    "-i", "temp_video.mp4",
    "-i", audio_file,
    "-c:v", "libx264",
    "-c:a", "aac",
    "-shortest",
    video_file
]

subprocess.run(ffmpeg_command, check=True)

# -----------------------------
# Send video to Telegram
# -----------------------------
with open(video_file, "rb") as f:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"video": f})

print(f"✅ MP4 generated and sent to Telegram: {video_file}")
