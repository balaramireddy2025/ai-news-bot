import os
import logging
from datetime import datetime
from ai_news import AINewsWorkflow
from gtts import gTTS
import requests
from moviepy.editor import *

# ------------------------
# Setup logging
# ------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ------------------------
# Load environment variables
# ------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ------------------------
# Validate secrets
# ------------------------
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY environment variable not set!")
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.warning("⚠️ Telegram credentials missing — Telegram posting will be skipped.")

# ------------------------
# Initialize AI News Workflow
# ------------------------
workflow = AINewsWorkflow(
    GEMINI_API_KEY,
    LINKEDIN_ACCESS_TOKEN,
    telegram_bot_token=TELEGRAM_BOT_TOKEN,
    telegram_chat_id=TELEGRAM_CHAT_ID
)

# ------------------------
# Function to convert text to speech
# ------------------------
def text_to_speech(news_text, filename="daily_news.mp3"):
    tts = gTTS(text=news_text, lang='en')
    tts.save(filename)
    logger.info(f"🎤 Generated TTS audio: {filename}")
    return filename

# ------------------------
# Function to create video with TTS audio and text overlay
# ------------------------
def create_news_video(news_text, audio_file, output_file="daily_news_video.mp4"):
    # Duration based on audio length
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration

    # Video clip: solid color background
    clip = ColorClip(size=(1280, 720), color=(10, 10, 50)).set_duration(duration)

    # Add scrolling headlines/text overlay
    txt_clip = TextClip(news_text, fontsize=40, color='white', font='Arial', method='caption', size=(1200, 600))
    txt_clip = txt_clip.set_position('center').set_duration(duration)

    # Combine video and text
    video = CompositeVideoClip([clip, txt_clip])
    video = video.set_audio(audio_clip)
    video.write_videofile(output_file, fps=24, codec='libx264')
    logger.info(f"🎬 Created news video: {output_file}")
    return output_file

# ------------------------
# Function to post video to Telegram
# ------------------------
def post_to_telegram(video_file_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram credentials missing — skipping post")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(video_file_path, "rb") as video:
        files = {"video": video}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "📢 Daily AI News Video"}
        response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        logger.info("✅ Posted video to Telegram successfully")
    else:
        logger.error(f"❌ Failed to post video to Telegram: {response.text}")

# ------------------------
# Main workflow
# ------------------------
def main():
    logger.info("⏰ Running AI News workflow...")

    # Generate AI news text
    result = workflow.create_daily_ai_news_post()
    logger.info(f"✅ Post result: {result['status']} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    news_text = result.get("text") or "Here are today's AI news highlights."

    # Generate TTS audio
    audio_file = text_to_speech(news_text)

    # Create news video
    video_file = create_news_video(news_text, audio_file)

    # Post to Telegram
    post_to_telegram(video_file)

# ------------------------
# Run main
# ------------------------
if __name__ == "__main__":
    main()
