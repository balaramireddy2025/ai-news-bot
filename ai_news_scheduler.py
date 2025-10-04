import os
import sys
import subprocess
from datetime import datetime

# Dependency check
try:
    import cv2
    import numpy as np
    import requests
    from gtts import gTTS
except ImportError as e:
    print(f"❌ Missing Python package: {e.name}")
    sys.exit(1)

# Check FFmpeg availability
try:
    subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.DEVNULL)
except FileNotFoundError:
    print("❌ FFmpeg is not installed or not in PATH")
    sys.exit(1)

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
    sys.exit(1)

# News text (placeholder)
news_text = "AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch."

# Convert text to speech
audio_file = "news.mp3"
tts = gTTS(text=news_text, lang="en")
tts.save(audio_file)

# Create video frames
width, height = 1280, 720
fps = 24
duration = 10  # seconds
num_frames = fps * duration

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_file = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
out = cv2.VideoWriter(video_file, fourcc, fps, (width, height))

for i in range(num_frames):
    # black background
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # add text in white at center
    cv2.putText(frame, news_text, (50, height // 2), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 2, cv2.LINE_AA)
    out.write(frame)

out.release()

# Add audio using FFmpeg
final_output = f"final_{video_file}"
cmd = [
    "ffmpeg", "-y",
    "-i", video_file,
    "-i", audio_file,
    "-c:v", "copy",
    "-c:a", "aac",
    "-shortest",
    final_output
]
subprocess.run(cmd, check=True)

# Send to Telegram
with open(final_output, "rb") as f:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"video": f})

print(f"✅ Video generated and sent to Telegram: {final_output}")
