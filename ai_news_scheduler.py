import os
import cv2
import numpy as np
from gtts import gTTS
import requests
import subprocess
from datetime import datetime
import time 
import sys

# ------------------------------
# Quick FFmpeg check (We exit if it fails)
# ------------------------------
try:
    # Use DEVNULL to suppress output
    subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    sys.exit("FFmpeg not installed or not in PATH. Check scheduler.yml.")

# ------------------------------
# Telegram config
# ------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    sys.exit("Telegram token or chat ID not set in environment.")

# ------------------------------
# AI News content
# ------------------------------
news_text = """
🔔 AI News Daily - Your update for today! 🔔

AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch.

Watch the video report below for the full story!
"""

# ------------------------------
# Convert text to speech (Using gTTS for now)
# ------------------------------
audio_file = "news.mp3"
# Use clean text for gTTS generation (excluding the video instructions)
gtts_text = "\n".join(news_text.splitlines()[:-1]).strip()
tts = gTTS(text=gtts_text, lang="en")
tts.save(audio_file)

# ------------------------------
# Create video with OpenCV
# ------------------------------
width, height = 1280, 720
fps = 24
duration = 15  # seconds - FORCED DURATION
num_frames = fps * duration

output_file = f"temp_ai_news_video.mp4" 
# Use 'mp4v' for the intermediate video.
fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
video_writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1.5
color = (255, 255, 255)
thickness = 2
bg_color = (0, 0, 0)
display_text = gtts_text

for _ in range(num_frames):
    frame = np.full((height, width, 3), bg_color, dtype=np.uint8)
    y0, dy = height // 2, 50
    
    # Render the text
    lines = display_text.split('\n')
    # Center the block of text
    text_height = len(lines) * dy
    start_y = y0 - text_height // 2 
    
    for i, line in enumerate(lines):
        if line.strip():
            y = start_y + i * dy
            cv2.putText(frame, line.strip(), (50, y), font, font_scale, color, thickness, cv2.LINE_AA)
            
    video_writer.write(frame)

video_writer.release()

# ------------------------------
# Merge and re-encode audio/video using FFmpeg (FORCED DURATION FIX)
# ------------------------------
final_output = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
print(f"Starting FFmpeg to create a {duration}-second video...")

subprocess.run([
    'ffmpeg', '-y',
    '-i', output_file, # Input video (15 seconds)
    '-i', audio_file,  # Input audio (e.g., 9 seconds)
    '-c:v', 'libx264',     # CRITICAL: Re-encode video stream
    '-preset', 'veryfast', # Faster encoding speed
    '-pix_fmt', 'yuv420p', # Standard pixel format
    '-c:a', 'aac',         # Use AAC for audio
    '-b:a', '192k',
    '-t', '15.0',          # <-- CRITICAL FIX: FORCES DURATION TO 15.0 SECONDS
    final_output
], check=True)

print(f"✅ Video created: {final_output}")
os.remove(output_file)

# ------------------------------
# 1. Send TEXT MESSAGE to Telegram with robust error logging (FIX)
# ------------------------------
print("--- Attempting to send text message to Telegram... ---")
text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
response = requests.post(text_url, data={
    "chat_id": TELEGRAM_CHAT_ID, 
    "text": news_text,
    "parse_mode": "Markdown" 
})

if response.status_code == 200:
    print("✅ Text message sent successfully.")
else:
    print(f"❌ Error sending text message. Status Code: {response.status_code}")
    print(f"Response: {response.text}") # Print full response for debugging

time.sleep(1) # Pause to ensure the text message posts first

# ------------------------------
# 2. Send VIDEO to Telegram with robust error logging
# ------------------------------
print("--- Attempting to send video to Telegram... ---")
with open(final_output, "rb") as f:
    video_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    video_caption = f"Full AI News Report - {datetime.now().strftime('%Y-%m-%d')}"
    
    response = requests.post(video_url, data={
        "chat_id": TELEGRAM_CHAT_ID, 
        "caption": video_caption
    }, files={"video": f})

if response.status_code == 200:
    print(f"✅ Video sent successfully.")
else:
    print(f"❌ Error sending video. Status Code: {response.status_code}")
    print(f"Response: {response.text}") # Print full response for debugging

# Final cleanup
os.remove(final_output)
os.remove(audio_file)
