import os
import cv2
import numpy as np
from gtts import gTTS
import subprocess
from datetime import datetime
import requests

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# AI News content
news_text = """
AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch.
"""

# Convert text to speech
audio_file = "news.mp3"
tts = gTTS(text=news_text, lang="en")
tts.save(audio_file)

# Video settings
width, height = 1280, 720
fps = 24
duration = 15  # seconds
frame_count = fps * duration

# Create a black background video with text
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1
color = (255, 255, 255)  # white text
thickness = 2

video_file = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_writer = cv2.VideoWriter(video_file, fourcc, fps, (width, height))

# Split text into lines that fit the screen
words = news_text.split()
lines = []
line = ""
for word in words:
    if len(line + " " + word) < 60:
        line += " " + word
    else:
        lines.append(line.strip())
        line = word
lines.append(line.strip())

for i in range(frame_count):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    y0 = height // 2 - (len(lines) * 30) // 2
    for j, l in enumerate(lines):
        y = y0 + j * 60
        cv2.putText(frame, l, (50, y), font, font_scale, color, thickness, cv2.LINE_AA)
    video_writer.write(frame)

video_writer.release()

# Merge audio with video using FFmpeg
final_output = f"final_{video_file}"
subprocess.run([
    "ffmpeg", "-y", "-i", video_file, "-i", audio_file, "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", final_output
], check=True)

# Send to Telegram
with open(final_output, "rb") as f:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"video": f})

print(f"✅ Video generated and sent: {final_output}")
