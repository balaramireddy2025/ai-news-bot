import os
import time
import schedule
import logging
from datetime import datetime
from gtts import gTTS
from moviepy.editor import TextClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from ai_news import AINewsWorkflow  # 👈 your AI news generator
import requests

# -----------------------------
# CONFIGURATION
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8042497508")
VIDEO_OUTPUT_FILE = "daily_ai_news_tv.mp4"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize workflow
workflow = AINewsWorkflow(
    GEMINI_API_KEY,
    LINKEDIN_ACCESS_TOKEN,
    telegram_bot_token=TELEGRAM_BOT_TOKEN,
    telegram_chat_id=TELEGRAM_CHAT_ID
)

# -----------------------------
# VIDEO CREATION FUNCTIONS
# -----------------------------
def generate_tts_audio(text, filename="news_audio.mp3"):
    logger.info("🎤 Generating TTS audio...")
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    logger.info(f"✅ TTS audio saved as {filename}")
    return filename

def create_news_clip(text, audio_file, width=1280, height=720, fontsize=40, duration_per_slide=8):
    logger.info("🎬 Creating video slides...")
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    clips = []

    for i, paragraph in enumerate(paragraphs):
        logger.info(f"  ➤ Processing slide {i+1}/{len(paragraphs)}")
        # Create text clip
        txt_clip = TextClip(paragraph, fontsize=fontsize, color='white', size=(width-100, None), method='caption')
        txt_clip = txt_clip.set_duration(duration_per_slide).set_position(('center', 'center')).on_color(color=(0,0,0), col_opacity=1)

        # Create scrolling ticker
        ticker_text = paragraph[:80] + " ..."  # first 80 chars
        ticker_clip = TextClip(ticker_text, fontsize=24, color='yellow', size=(width*2, 30), method='caption')
        ticker_clip = ticker_clip.set_duration(duration_per_slide).set_position(('left', height-40))
        ticker_clip = ticker_clip.set_start(0).fx(lambda c: c.set_position(lambda t: ('center', height-40)))

        # Composite slide
        clip = CompositeVideoClip([txt_clip, ticker_clip])
        clips.append(clip)

    # Concatenate all slides
    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_file)
    video = video.set_audio(audio)
    logger.info("✅ All slides processed, video ready.")
    return video

# -----------------------------
# SCHEDULED JOB
# -----------------------------
def job():
    logger.info("⏰ Running AI News workflow...")
    result = workflow.create_daily_ai_news_post()
    news_content = result['generated_content'].content

    # Generate audio
    audio_file = generate_tts_audio(news_content, "news_audio.mp3")

    # Create video
    video = create_news_clip(news_content, audio_file)
    logger.info("💾 Writing video file...")
    video.write_videofile(VIDEO_OUTPUT_FILE, fps=24, codec="libx264", audio_codec="aac", verbose=True, progress_bar=True)
    logger.info(f"✅ Video generated: {VIDEO_OUTPUT_FILE}")

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        logger.info(f"📤 Sending video to Telegram chat {TELEGRAM_CHAT_ID}...")
        with open(VIDEO_OUTPUT_FILE, 'rb') as f:
            files = {'video': f}
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo?chat_id={TELEGRAM_CHAT_ID}"
            r = requests.post(url, files=files)
        if r.status_code == 200:
            logger.info("✅ Video sent to Telegram successfully!")
        else:
            logger.warning(f"❌ Failed to send video to Telegram: {r.text}")

# -----------------------------
# SCHEDULER
# -----------------------------
schedule.every().day.at("10:00").do(job)
logger.info("📅 Scheduler started. Waiting for 10:00 each day...")

while True:
    schedule.run_pending()
    time.sleep(60)
