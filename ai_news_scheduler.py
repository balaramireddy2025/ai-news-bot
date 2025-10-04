import os
import cv2
import numpy as np
# NOTE: gTTS is still required by requirements.txt but not used for audio generation
# from gtts import gTTS 
import requests
import subprocess
from datetime import datetime
import time # Import time for a small pause between messages

# ------------------------------
# Quick FFmpeg check (Remains for verification, even though we install it now)
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

(The full video is below!)
"""

# ------------------------------
# Audio setup (USING YOUR PRE-RECORDED FILE)
# ------------------------------
# *** IMPORTANT: Make sure this file exists in your repository root ***
audio_file = "my_news_narration.mp3" 

if not os.path.exists(audio_file):
    # FALLBACK: If the user hasn't provided their voice, use gTTS
    print(f"⚠️ Custom audio file '{audio_file}' not found. Falling back to gTTS.")
    from gtts import gTTS
    gtts_text = news_text.replace("(The full video is below!)", "").strip() # Use clean text for gTTS
    tts = gTTS(text=gtts_text, lang="en")
    tts.save(audio_file)

# ------------------------------
# Create video with OpenCV
# We need to find the actual duration of the audio file here
# ------------------------------
try:
    # Use ffprobe to get audio duration (more reliable than fixed 15s)
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_file],
        capture_output=True, text=True, check=True
    )
    duration = float(result.stdout.strip())
    print(f"Audio duration detected: {duration:.2f} seconds")
except Exception as e:
    print(f"Warning: Could not determine audio duration with ffprobe. Using default 15 seconds. Error: {e}")
    duration = 15

width, height = 1280, 720
fps = 24
num_frames = max(1, int(fps * duration))

# Prepare video writer
output_file = f"temp_ai_news_video.mp4" 
fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
video_writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

# Prepare text for frames
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1.5
color = (255, 255, 255)
thickness = 2
bg_color = (0, 0, 0)
display_text = news_text.replace("(The full video is below!)", "").strip() # Text to display on video

for _ in range(num_frames):
    frame = np.full((height, width, 3), bg_color, dtype=np.uint8)
    y0, dy = height // 2, 50
    # Simple logic to display the main news sentence
    lines = display_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip(): # Skip empty lines
            y = y0 + i * dy - (len(lines) * dy // 2)
            cv2.putText(frame, line.strip(), (50, y), font, font_scale, color, thickness, cv2.LINE_AA)
    video_writer.write(frame)

video_writer.release()

# ------------------------------
# Merge and re-encode audio/video using FFmpeg for compatibility
# ------------------------------
final_output = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

# FFmpeg command (optimized for Telegram/H.264)
subprocess.run([
    'ffmpeg', '-y',
    '-i', output_file, # Input video (from OpenCV)
    '-i', audio_file,  # Input audio (Your MP3 or gTTS fallback)
    '-c:v', 'libx264', # Encode video to H.264 (robust codec)
    '-preset', 'veryfast', # Faster encoding speed
    '-pix_fmt', 'yuv420p', # Standard pixel format for maximum compatibility
    '-c:a', 'aac',     # Encode audio to AAC (standard for MP4)
    '-b:a', '192k',    # Audio bitrate
    '-shortest',       # Finish encoding when the shortest input stream (audio) ends
    final_output
], check=True)

# Clean up temporary video file
os.remove(output_file)
# Note: Keep audio_file until we send the text message for the full caption

# ------------------------------
# Send *TEXT MESSAGE* to Telegram first
# ------------------------------
print("Sending text message to Telegram...")
text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
requests.post(text_url, data={
    "chat_id": TELEGRAM_CHAT_ID, 
    "text": news_text, # Send the full text with the initial message
    "parse_mode": "Markdown" # Allows for bold/emoji formatting in the text
})
time.sleep(1) # Add a small pause to ensure messages arrive in correct order

# ------------------------------
# Send *VIDEO* to Telegram
# ------------------------------
print("Sending video to Telegram...")
with open(final_output, "rb") as f:
    video_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    # The caption for the video will just be a quick tag
    video_caption = f"Full AI News Report - {datetime.now().strftime('%Y-%m-%d')}"
    
    requests.post(video_url, data={
        "chat_id": TELEGRAM_CHAT_ID, 
        "caption": video_caption
    }, files={"video": f})

print(f"✅ Text message and video sent to Telegram: {final_output}")

# Final cleanup
os.remove(final_output)
os.remove(audio_file)
