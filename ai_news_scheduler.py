import os
import time
import schedule
import logging
from datetime import datetime
from gtts import gTTS
from moviepy.editor import (
    TextClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, ColorClip
)
import requests

# -----------------------------
# CONFIGURATION
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", None)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8042497508")
VIDEO_OUTPUT_FILE = "daily_ai_news_tv.mp4"
VIDEO_WIDTH, VIDEO_HEIGHT = 1280, 720
FONT_SIZE = 40
DURATION_PER_SLIDE = 8  # seconds

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# -----------------------------
# FAKE AI NEWS WORKFLOW (Replace with your own AI generator)
# -----------------------------
class AINewsWorkflow:
    def __init__(self, api_key, linkedin_token=None, telegram_bot_token=None, telegram_chat_id=None):
        self.api_key = api_key
        self.linkedin_token = linkedin_token
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

    def create_daily_ai_news_post(self):
        # This should be replaced by your real Gemini/AI workflow
        content = (
            "🚀 AI for a Greener Tomorrow: Mitti Labs empowers Indian rice farmers.\n\n"
            "📡 Unlocking New Business Models: China Mobile & Huawei 5G-A demo.\n\n"
            "💡 Cultivating Next-Gen Innovators: MIT welcomes Ana Bakshi.\n\n"
            "Actionable insights:\n* Embrace AI for ESG\n* Strategize for 5G-A\n* Invest in ecosystems"
        )
        return {
            'generated_content': type('obj', (object,), {'content': content}),
            'trending_topics': ['AI startup']
        }

workflow = AINewsWorkflow(GEMINI_API_KEY, LINKEDIN_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

# -----------------------------
# VIDEO CREATION FUNCTIONS
# -----------------------------
def generate_tts_audio(text, filename="news_audio.mp3"):
    logger.info("🔊 Generating TTS audio...")
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    return filename

def create_news_clip(text, audio_file, width=VIDEO_WIDTH, height=VIDEO_HEIGHT,
                      fontsize=FONT_SIZE, duration_per_slide=DURATION_PER_SLIDE):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    clips = []

    for i, paragraph in enumerate(paragraphs, start=1):
        logger.info(f"🎬 Creating slide {i}/{len(paragraphs)}: {paragraph[:50]}...")

        # Background color clip
        bg_clip = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration_per_slide)

        # Main text clip
        txt_clip = TextClip(paragraph, fontsize=fontsize, color='white',
                            size=(width-100, None), method='label')
        txt_clip = txt_clip.set_position(('center', 'center')).set_duration(duration_per_slide)

        # Scrolling ticker at bottom
        ticker_text = paragraph[:120] + " ... "  # first 120 chars for ticker
        ticker_clip = TextClip(ticker_text, fontsize=24, color='yellow', method='label')
        ticker_clip = ticker_clip.set_position(lambda t: (int(width - t*100) % width, height-50)).set_duration(duration_per_slide)

        # Composite
        slide = CompositeVideoClip([bg_clip, txt_clip, ticker_clip])
        clips.append(slide)

    # Concatenate all slides
    final_video = concatenate_videoclips(clips, method="compose")

    # Add audio
    audio = AudioFileClip(audio_file)
    final_video = final_video.set_audio(audio)

    return final_video

# -----------------------------
# SCHEDULED JOB
# -----------------------------
def job():
    logger.info("⏰ Running AI News workflow...")
    result = workflow.create_daily_ai_news_post()
    news_content = result['generated_content'].content

    # Generate audio
    audio_file = generate_tts_audio(news_content)

    # Create video
    video = create_news_clip(news_content, audio_file)
    logger.info("💾 Writing MP4 video...")
    video.write_videofile(VIDEO_OUTPUT_FILE, fps=24, codec='libx264', audio_codec='aac')
    logger.info(f"✅ Video generated: {VIDEO_OUTPUT_FILE}")

    # Telegram upload
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        logger.info(f"📤 Sending video to Telegram chat {TELEGRAM_CHAT_ID}...")
        with open(VIDEO_OUTPUT_FILE, 'rb') as f:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo?chat_id={TELEGRAM_CHAT_ID}"
            r = requests.post(url, files={'video': f})
        if r.status_code == 200:
            logger.info("✅ Video sent successfully to Telegram")
        else:
            logger.warning(f"❌ Failed to send video: {r.text}")

# -----------------------------
# SCHEDULER
# -----------------------------
schedule.every().day.at("10:00").do(job)
logger.info("📅 Scheduler started. Waiting for 10:00 each day...")

while True:
    schedule.run_pending()
    time.sleep(30)
