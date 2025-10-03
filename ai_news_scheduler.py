# ai_news_scheduler.py
import os
import requests
from gtts import gTTS
from moviepy.video.VideoClip import TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set in GitHub Secrets
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # Set in GitHub Secrets
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 480
VIDEO_DURATION = 5  # seconds per clip
FPS = 24

# -----------------------------
# AI NEWS CONTENT (demo)
# Replace this with actual AI-generated content if you want
# -----------------------------
news_items = [
    "AI is revolutionizing healthcare, education, and finance.",
    "5G and AI convergence is creating new business opportunities.",
    "Entrepreneurs are using AI to scale sustainability projects globally."
]

def create_video_clip(text, duration=VIDEO_DURATION):
    """Create a single video clip with text and TTS audio"""
    # Background clip
    bg = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(20, 20, 20), duration=duration)

    # Text clip (MoviePy 2.1.1, method='caption' avoids ImageMagick)
    txt = TextClip(text, fontsize=40, color='white', method='caption', size=(VIDEO_WIDTH-20, VIDEO_HEIGHT-20))
    txt = txt.set_position("center").set_duration(duration)

    # Combine
    clip = CompositeVideoClip([bg, txt])

    # Create TTS audio
    tts = gTTS(text)
    tts_file = "tts.mp3"
    tts.save(tts_file)
    audio = AudioFileClip(tts_file)
    clip = clip.set_audio(audio)

    return clip

def generate_news_video(news_items):
    clips = [create_video_clip(text) for text in news_items]
    final_video = concatenate_videoclips(clips, method="compose")
    
    output_file = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    final_video.write_videofile(output_file, fps=FPS, codec="libx264")
    return output_file

def post_to_telegram(video_file, bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID):
    """Send MP4 video to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    with open(video_file, "rb") as f:
        files = {"video": f}
        data = {"chat_id": chat_id, "caption": "Today's AI News"}
        r = requests.post(url, files=files, data=data)
    return r.json()

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("⏰ Running AI News Scheduler...")
    video_file = generate_news_video(news_items)
    print(f"✅ Video generated: {video_file}")
    
    response = post_to_telegram(video_file)
    print(f"✅ Telegram response: {response}")
