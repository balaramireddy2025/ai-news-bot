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
def text_to_speech(news_text, filename):
    tts = gTTS(text=news_text, lang='en')
    tts.save(filename)
    logger.info(f"🎤 Generated TTS audio: {filename}")
    return filename

# ------------------------
# Function to create a TV-style video segment
# ------------------------
def create_segment_video(segment_text, segment_index, audio_file):
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration

    # Base clip: 1280x720 dark blue background
    clip = ColorClip(size=(1280, 720), color=(10, 10, 50)).set_duration(duration)

    # Center main news text
    main_text = TextClip(segment_text, fontsize=50, color='white', font='Arial-Bold',
                         method='caption', size=(1100, 500))
    main_text = main_text.set_position('center').set_duration(duration)

    # Scrolling ticker at bottom
    ticker_text = TextClip(segment_text + " — " + segment_text, fontsize=30, color='yellow', font='Arial-Bold',
                           method='caption', size=(3000, 60))
    ticker = ticker_text.set_position(lambda t: (1280 - t*200, 650)).set_duration(duration)

    # Combine clip + main text + ticker
    final_clip = CompositeVideoClip([clip, main_text, ticker])
    final_clip = final_clip.set_audio(audio_clip)

    return final_clip

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
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "📢 Daily AI News Broadcast"}
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
    logger.info(f"✅ AI News status: {result['status']} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    full_news_text = result.get("text") or "Here are today's AI news highlights."

    # Split into segments (simple split by sentences for demo)
    news_segments = [seg.strip() for seg in full_news_text.split('.') if seg.strip()]
    if not news_segments:
        news_segments = [full_news_text]

    video_clips = []

    # Process each segment
    for i, segment in enumerate(news_segments):
        audio_file = f"segment_{i}.mp3"
        text_to_speech(segment, audio_file)
        clip = create_segment_video(segment, i, audio_file)
        video_clips.append(clip)

    # Concatenate all segments
    final_video = concatenate_videoclips(video_clips, method="compose")
    output_file = "daily_ai_news_broadcast.mp4"
    final_video.write_videofile(output_file, fps=24, codec="libx264")
    logger.info(f"🎬 Created final news broadcast video: {output_file}")

    # Post video to Telegram
    post_to_telegram(output_file)

# ------------------------
# Run main
# ------------------------
if __name__ == "__main__":
    main()
