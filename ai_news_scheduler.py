#!/usr/bin/env python3
# ai_news_scheduler.py
import os
import schedule
import time
import requests
from gtts import gTTS

# Correct MoviePy 2.1.1 imports
from moviepy.video.VideoClip import ColorClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.audio.io.AudioFileClip import AudioFileClip

# ----------------------------
# Configurations
# ----------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

VIDEO_OUTPUT = "news.mp4"
AUDIO_OUTPUT = "news.mp3"

# ----------------------------
# Example: AI News fetcher
# Replace this with your own AI-generated content
# ----------------------------
def fetch_ai_news():
    # Placeholder for AI news text
    return "Hello! This is today's AI news update. AI is changing the world every day!"

# ----------------------------
# Generate TTS audio
# ----------------------------
def generate_audio(text):
    tts = gTTS(text)
    tts.save(AUDIO_OUTPUT)
    print(f"[INFO] Audio saved: {AUDIO_OUTPUT}")

# ----------------------------
# Generate MP4 video
# ----------------------------
def generate_video(text):
    print("[INFO] Generating video...")

    # Create TextClip for text overlay
    txt_clip = TextClip(text, fontsize=40, color='white', size=(720, 480), method='caption', align='center')
    
    # Background color clip
    bg_clip = ColorClip(size=(720, 480), color=(0, 0, 128), duration=txt_clip.duration)
    
    # Composite video with text overlay
    video = CompositeVideoClip([bg_clip, txt_clip.set_position('center')])
    
    # Add audio
    audio = AudioFileClip(AUDIO_OUTPUT)
    video = video.set_audio(audio)
    
    # Write MP4 file
    video.write_videofile(VIDEO_OUTPUT, fps=24)
    print(f"[INFO] Video saved: {VIDEO_OUTPUT}")

# ----------------------------
# Send to Telegram
# ----------------------------
def send_to_telegram():
    print("[INFO] Sending video to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(VIDEO_OUTPUT, "rb") as f:
        files = {"video": f}
        data = {"chat_id": TELEGRAM_CHAT_ID}
        resp = requests.post(url, data=data, files=files)
        if resp.status_code == 200:
            print("[INFO] Video sent to Telegram successfully!")
        else:
            print(f"[ERROR] Failed to send video: {resp.text}")

# ----------------------------
# Main scheduler job
# ----------------------------
def job():
    print("[INFO] Running AI News workflow...")
    news_text = fetch_ai_news()
    generate_audio(news_text)
    generate_video(news_text)
    send_to_telegram()
    print("[INFO] Workflow completed.")

# ----------------------------
# Schedule: run daily at 09:30 UTC
# ----------------------------
schedule.every().day.at("09:30").do(job)

print("[INFO] Scheduler started...")
while True:
    schedule.run_pending()
    time.sleep(30)
