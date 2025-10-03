import os
import time
import schedule
import logging
from gtts import gTTS
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
from ai_news import AINewsWorkflow  # Your AI news workflow

# -----------------------------
# CONFIGURATION
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8042497508")
VIDEO_OUTPUT_FILE = "daily_ai_news.mp4"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize AI workflow
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
    return filename

def create_news_video(text, audio_file, width=1280, height=720, fontsize=50, duration_per_slide=6):
    logger.info("🎬 Creating video slides...")
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    slides = []

    for i, paragraph in enumerate(paragraphs, start=1):
        logger.info(f"  ➤ Creating slide {i}/{len(paragraphs)}")
        # Background
        bg = ColorClip((width, height), color=(0, 0, 0), duration=duration_per_slide)
        # Text clip
        txt_clip = TextClip(paragraph, fontsize=fontsize, color='white', size=(width-100, None), method='label')
        txt_clip = txt_clip.set_position('center').set_duration(duration_per_slide)
        # Composite
        slide = CompositeVideoClip([bg, txt_clip])
        slides.append(slide)

    video = concatenate_videoclips(slides)
    audio = AudioFileClip(audio_file)
    video = video.set_audio(audio)

    return video

# -----------------------------
# SCHEDULED JOB
# -----------------------------
def job():
    logger.info("⏰ Running AI News workflow...")

    # Generate AI news
    result = workflow.create_daily_ai_news_post()
    news_content = result['generated_content'].content
    logger.info(f"✅ AI news generated: {len(news_content)} chars")

    # Generate TTS audio
    audio_file = generate_tts_audio(news_content)

    # Generate video
    video = create_news_video(news_content, audio_file)
    logger.info("💾 Rendering MP4...")
    video.write_videofile(VIDEO_OUTPUT_FILE, fps=24, codec='libx264', audio_codec='aac')
    logger.info(f"✅ Video generated: {VIDEO_OUTPUT_FILE}")

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        import requests
        logger.info("📲 Sending video to Telegram...")
        with open(VIDEO_OUTPUT_FILE, 'rb') as f:
            files = {'video': f}
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
