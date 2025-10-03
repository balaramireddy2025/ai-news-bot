import os
import time
import schedule
import logging
from datetime import datetime
from gtts import gTTS
from moviepy.editor import TextClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, VideoClip
from ai_news import AINewsWorkflow  # 👈 Your AI news generator
import requests
from pydub import AudioSegment

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
def generate_tts_audio(paragraphs, filename="news_audio.mp3"):
    """Generate TTS audio from a list of paragraphs."""
    combined = AudioSegment.empty()
    for i, text in enumerate(paragraphs):
        tts_file = f"tts_temp_{i}.mp3"
        tts = gTTS(text=text, lang='en')
        tts.save(tts_file)
        combined += AudioSegment.from_mp3(tts_file)
        os.remove(tts_file)
    combined.export(filename, format="mp3")
    return filename

def scrolling_ticker(text, width=1280, height=720, fontsize=24, duration=8):
    """Create a scrolling ticker at the bottom."""
    txt_clip = TextClip(text, fontsize=fontsize, color='yellow', size=(None, 30), method='caption')
    txt_w, txt_h = txt_clip.size

    def make_frame(t):
        x = width - (t * 100) % (width + txt_w)  # scroll speed: 100 px/sec
        frame = txt_clip.get_frame(0)
        return frame

    return VideoClip(make_frame, duration=duration).set_position(('left', height-30))

def create_news_clip(text, audio_file, width=1280, height=720, fontsize=40):
    """Create video slides with text and ticker."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    clips = []

    # Generate video slides
    for paragraph in paragraphs:
        duration = max(5, len(paragraph)/20)  # 1 sec per 20 chars, min 5 sec
        txt_clip = TextClip(paragraph, fontsize=fontsize, color='white', size=(width-100, None), method='caption')
        txt_clip = txt_clip.set_duration(duration).set_position(('center', 'center')).on_color(color=(0,0,0), col_opacity=1)

        ticker_clip = TextClip(paragraph[:120], fontsize=24, color='yellow', size=(width, 30), method='caption')
        ticker_clip = ticker_clip.set_duration(duration).set_position(('left', height-40))

        clip = CompositeVideoClip([txt_clip, ticker_clip])
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_file)
    video = video.set_audio(audio)

    return video

# -----------------------------
# SCHEDULED JOB
# -----------------------------
def job():
    logger.info("⏰ Running AI News workflow...")

    # Fetch AI news
    result = workflow.create_daily_ai_news_post()
    news_content = result['generated_content'].content
    paragraphs = [p.strip() for p in news_content.split("\n") if p.strip()]

    # Generate audio
    audio_file = generate_tts_audio(paragraphs, "news_audio.mp3")

    # Create video
    video = create_news_clip(news_content, audio_file)
    video.write_videofile(VIDEO_OUTPUT_FILE, fps=24)

    logger.info(f"✅ Video generated: {VIDEO_OUTPUT_FILE}")

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
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
