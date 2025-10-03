# ai_news_scheduler.py
import os
import logging
from datetime import datetime
from gtts import gTTS
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip, AudioFileClip
import requests
import schedule
import time

# ---------------- CONFIG ----------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
VIDEO_OUTPUT_DIR = "videos"
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 480
VIDEO_BG_COLOR = (30, 30, 30)  # dark gray
VIDEO_DURATION_PER_SCREEN = 8  # seconds per text clip
FONT_SIZE = 40
FONT_COLOR = "white"
FONT = "Arial-Bold"  # MoviePy built-in font, no ImageMagick
# ---------------------------------------

logging.basicConfig(level=logging.INFO)
os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)

# ------------------ AI / News Fetching Stub ------------------
# Replace this function with your AI news generator (e.g., Google GenAI)
def fetch_ai_news():
    """
    Return a dict containing title and content text for the video.
    """
    return {
        "title": "AI & Tech Update: Innovation Across Industries",
        "content": (
            "1. AI is revolutionizing sustainable farming.\n"
            "2. 5G-A networks are unlocking immersive experiences.\n"
            "3. Entrepreneurship and AI are shaping the future."
        )
    }

# ------------------ Video Generation ------------------
def generate_video_from_text(news_data):
    logging.info("🎬 Generating video...")

    # Generate TTS audio
    tts = gTTS(text=news_data["content"], lang="en")
    audio_path = os.path.join(VIDEO_OUTPUT_DIR, "tts.mp3")
    tts.save(audio_path)

    # Split content into lines
    lines = news_data["content"].split("\n")
    clips = []

    for line in lines:
        txt_clip = TextClip(
            line,
            fontsize=FONT_SIZE,
            color=FONT_COLOR,
            font=FONT,
            size=(VIDEO_WIDTH - 40, None),
            method="caption"  # ensures proper wrapping
        )
        txt_clip = txt_clip.set_duration(VIDEO_DURATION_PER_SCREEN).set_position("center")
        bg_clip = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=VIDEO_BG_COLOR, duration=VIDEO_DURATION_PER_SCREEN)
        clips.append(CompositeVideoClip([bg_clip, txt_clip]))

    # Concatenate all text clips
    video = CompositeVideoClip(clips).set_duration(len(clips) * VIDEO_DURATION_PER_SCREEN)

    # Add audio
    audio_clip = AudioFileClip(audio_path)
    video = video.set_audio(audio_clip).set_duration(audio_clip.duration)

    # Export video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(VIDEO_OUTPUT_DIR, f"ai_news_{timestamp}.mp4")
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    logging.info(f"✅ Video generated at: {output_path}")
    return output_path

# ------------------ Telegram Posting ------------------
def send_to_telegram(video_path):
    logging.info("📤 Sending video to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(video_path, "rb") as f:
        files = {"video": f}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "Daily AI News Update"}
        resp = requests.post(url, data=data, files=files)
    if resp.status_code == 200:
        logging.info("✅ Video sent to Telegram successfully!")
    else:
        logging.error(f"❌ Failed to send video: {resp.text}")

# ------------------ Main Workflow ------------------
def run_workflow():
    logging.info("⏰ Running AI News workflow...")
    news = fetch_ai_news()
    video_file = generate_video_from_text(news)
    send_to_telegram(video_file)

# ------------------ Scheduler ------------------
schedule.every().day.at("04:40").do(run_workflow)  # UTC time for GitHub Actions

if __name__ == "__main__":
    logging.info("🟢 AI News Scheduler started.")
    while True:
        schedule.run_pending()
        time.sleep(10)
