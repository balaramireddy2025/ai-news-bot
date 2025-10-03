import os
import time
import schedule
import logging
from datetime import datetime
from gtts import gTTS
from moviepy.editor import TextClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from ai_news import AINewsWorkflow  # 👈 your AI news generator

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
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    return filename

def create_news_clip(text, audio_file, width=1280, height=720, fontsize=40, duration_per_slide=8):
    # Split text into chunks for slides
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    clips = []

    for paragraph in paragraphs:
        # Create text clip
        txt_clip = TextClip(paragraph, fontsize=fontsize, color='white', size=(width-100, None), method='caption')
        txt_clip = txt_clip.set_duration(duration_per_slide).set_position(('center', 'center')).on_color(color=(0,0,0), col_opacity=1)

        # Add ticker
        ticker_text = " | ".join([paragraph[:80]])  # simple ticker, first 80 chars
        ticker_clip = TextClip(ticker_text, fontsize=24, color='yellow', size=(width, 30), method='caption')
        ticker_clip = ticker_clip.set_duration(duration_per_slide).set_position(('left', height-40)).set_start(0)

        # Composite
        clip = CompositeVideoClip([txt_clip, ticker_clip])
        clips.append(clip)

    # Concatenate all clips
    video = concatenate_videoclips(clips, method="compose")

    # Add audio
    audio = AudioFileClip(audio_file)
    video = video.set_audio(audio)

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
    video.write_videofile(VIDEO_OUTPUT_FILE, fps=24)

    logger.info(f"✅ Video generated: {VIDEO_OUTPUT_FILE}")

    # Telegram (optional)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        import requests
        files = {'video': open(VIDEO_OUTPUT_FILE, 'rb')}
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo?chat_id={TELEGRAM_CHAT_ID}"
        r = requests.post(url, files=files)
        if r.status_code == 200:
            logger.info(f"✅ Video sent to Telegram chat {TELEGRAM_CHAT_ID}")
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
