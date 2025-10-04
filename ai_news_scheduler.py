import os
import cv2
import numpy as np
import subprocess
from gtts import gTTS
from datetime import datetime
import requests

# ------------------ CONFIG ------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# AI News content (placeholder)
news_text = "AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch."

# Output file names
audio_file = "news.mp3"
image_file = "news.png"
video_file = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

# ------------------ CREATE AUDIO ------------------
tts = gTTS(text=news_text, lang="en")
tts.save(audio_file)
print("✅ Audio generated.")

# ------------------ CREATE IMAGE ------------------
# Image size
width, height = 1280, 720
background_color = (0, 0, 0)  # Black

# Create black background
img = np.zeros((height, width, 3), dtype=np.uint8)
img[:] = background_color

# Add text to the image
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1
color = (255, 255, 255)  # White
thickness = 2
y0, dy = 100, 40

# Split text into lines if too long
words = news_text.split(' ')
lines = []
line = ""
for word in words:
    if len(line + ' ' + word) > 40:
        lines.append(line)
        line = word
    else:
        line += ' ' + word if line else word
if line:
    lines.append(line)

for i, line in enumerate(lines):
    y = y0 + i * dy
    text_size = cv2.getTextSize(line, font, font_scale, thickness)[0]
    x = (width - text_size[0]) // 2
    cv2.putText(img, line, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

cv2.imwrite(image_file, img)
print("✅ Image generated.")

# ------------------ CREATE VIDEO USING FFMPEG ------------------
# Get audio duration
audio_duration = subprocess.check_output(
    ["ffprobe", "-i", audio_file, "-show_entries", "format=duration",
     "-v", "quiet", "-of", "csv=p=0"]
).decode().strip()

# Run ffmpeg to make video from image + audio
ffmpeg_cmd = [
    "ffmpeg",
    "-loop", "1",
    "-i", image_file,
    "-i", audio_file,
    "-c:v", "libx264",
    "-tune", "stillimage",
    "-c:a", "aac",
    "-b:a", "192k",
    "-pix_fmt", "yuv420p",
    "-shortest",
    video_file
]

subprocess.run(ffmpeg_cmd, check=True)
print(f"✅ Video generated: {video_file}")

# ------------------ SEND TO TELEGRAM ------------------
with open(video_file, "rb") as f:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    response = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"video": f})

if response.status_code == 200:
    print("✅ Video sent to Telegram successfully.")
else:
    print("❌ Failed to send video to Telegram:", response.text)
