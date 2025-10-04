import os
import cv2
import numpy as np
from gtts import gTTS
import requests
import subprocess
from datetime import datetime
import time # Keep time for a small pause between messages

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
# AI News content
# ------------------------------
news_text = """
🔔 AI News Daily - Your update for today! 🔔

AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch.

(The full video report is below. Listen for the full voice narration!)
"""

# ------------------------------
# Convert text to speech (Using gTTS for now)
# ------------------------------
audio_file = "news.mp3"
# Use clean text for gTTS generation
gtts_text = news_text.replace("(The full video report is below. Listen for the full voice narration!)", "").strip() 
tts = gTTS(text=gtts_text, lang="en")
tts.save(audio_file)

# ------------------------------
# Create video with OpenCV
# ------------------------------
width, height = 1280, 720
fps = 24
# Set a fixed duration to ensure the text screen stays visible
duration = 15  # seconds
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
display_text = gtts_text # Text to display on video is the TTS text

for _ in range(num_frames):
    frame = np.full((height, width, 3), bg_color, dtype=np.uint8)
    y0, dy = height // 2, 50
    
    # Render the text
    lines = display_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip(): # Skip empty lines
            # Calculate position relative to the center
            y = y0 + i * dy - (len(lines) * dy // 2)
            cv2.putText(frame, line.strip(), (50, y), font, font_scale, color, thickness, cv2.LINE_AA)
            
    video_writer.write(frame)

video_writer.release()

# ------------------------------
# Merge and re-encode audio/video using FFmpeg for compatibility
# We REMOVE the -shortest flag to force the video to the full 15 seconds
# ------------------------------
final_output = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

subprocess.run([
    'ffmpeg', '-y',
    '-i', output_file, # Input video (15 seconds)
    '-i', audio_file,  # Input audio (e.g., 9 seconds)
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '192k',
    # '-shortest', <--- REMOVED: This forces video duration to match audio (which is short)
    '-t', str(duration), # Add duration command to ensure the video is the full length
    final_output
], check=True)

# Clean up temporary video file
os.remove(output_file)

# ------------------------------
# 1. Send TEXT MESSAGE to Telegram
# ------------------------------
print("Sending text message to Telegram...")
text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
response = requests.post(text_url, data={
    "chat_id": TELEGRAM_CHAT_ID, 
    "text": news_text, # Send the full text
    "parse_mode": "Markdown"
})
if response.status_code != 200:
    print(f"Error sending text message: {response.text}")

time.sleep(1) # Pause to ensure the text message posts first

# ------------------------------
# 2. Send VIDEO to Telegram
# ------------------------------
print("Sending video to Telegram...")
with open(final_output, "rb") as f:
    video_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    video_caption = f"Full AI News Report - {datetime.now().strftime('%Y-%m-%d')}"
    
    response = requests.post(video_url, data={
        "chat_id": TELEGRAM_CHAT_ID, 
        "caption": video_caption
    }, files={"video": f})

if response.status_code != 200:
    print(f"Error sending video: {response.text}")

print(f"✅ Text message and video successfully processed: {final_output}")

# Final cleanup
os.remove(final_output)
os.remove(audio_file)
