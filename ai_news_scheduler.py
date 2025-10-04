import os
import cv2
import numpy as np
from gtts import gTTS
import requests
import subprocess
from datetime import datetime

# ------------------------------
# Quick FFmpeg check
# ------------------------------
try:
    # Use DEVNULL to suppress output, keeping the check clean
    subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL)
except FileNotFoundError:
    raise SystemExit("FFmpeg not installed or not in PATH.")

# ------------------------------
# Telegram config
# ------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise SystemExit("Telegram token or chat ID not set in environment.")

# ------------------------------
# AI News content (placeholder)
# ------------------------------
# The script will now handle dynamic news content generation here
news_text = """
AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch.
"""

# ------------------------------
# Convert text to speech
# ------------------------------
audio_file = "news.mp3"
tts = gTTS(text=news_text, lang="en")
tts.save(audio_file)

# ------------------------------
# Create video with OpenCV
# ------------------------------
width, height = 1280, 720
fps = 24
# Determine duration based on audio file length (placeholder: using a fixed duration)
duration = 15  # seconds (This should be adjusted to match audio length in a production script)
num_frames = fps * duration

# Prepare video writer
output_file = f"temp_ai_news_video.mp4" 
# Use 'mp4v' for the intermediate video. The next step will re-encode.
fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
video_writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

# Prepare text for frames
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1.5
color = (255, 255, 255)
thickness = 2
bg_color = (0, 0, 0)

for _ in range(num_frames):
    frame = np.full((height, width, 3), bg_color, dtype=np.uint8)
    y0, dy = height // 2, 50
    for i, line in enumerate(news_text.strip().split('\n')):
        # Simple text drawing - consider multi-line rendering for long text
        y = y0 + i * dy
        cv2.putText(frame, line, (50, y), font, font_scale, color, thickness, cv2.LINE_AA)
    video_writer.write(frame)

video_writer.release()

# ------------------------------
# Merge and re-encode audio/video using FFmpeg for compatibility
# ------------------------------
final_output = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
# Explicitly re-encode video to H.264 (libx264) and audio to AAC
subprocess.run([
    'ffmpeg', '-y',
    '-i', output_file, # Input video (from OpenCV)
    '-i', audio_file,  # Input audio (from gTTS)
    '-c:v', 'libx264', # Encode video to H.264 (robust codec)
    '-preset', 'veryfast', # Faster encoding speed
    '-pix_fmt', 'yuv420p', # Standard pixel format for maximum compatibility
    '-c:a', 'aac',     # Encode audio to AAC (standard for MP4)
    '-b:a', '192k',    # Audio bitrate
    '-shortest',       # Finish encoding when the shortest input stream (usually audio) ends
    final_output
], check=True)

# Clean up temporary video file
os.remove(output_file)
os.remove(audio_file)

# ------------------------------
# Send video to Telegram
# ------------------------------
with open(final_output, "rb") as f:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    caption = f"AI News Daily - {datetime.now().strftime('%Y-%m-%d')}"
    # Requests will automatically use multipart/form-data for files
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption}, files={"video": f})

print(f"✅ Video generated, re-encoded, and sent to Telegram: {final_output}")
