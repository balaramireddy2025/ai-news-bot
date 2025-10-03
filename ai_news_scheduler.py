import os
import logging
from datetime import datetime
from ai_news import AINewsWorkflow   # your existing AI news workflow
from gtts import gTTS
import requests

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
    logger.warning("⚠️ Telegram secrets missing — Telegram posting will be skipped.")

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
# Function to convert news text to speech
# ------------------------
def text_to_speech(news_text, filename="daily_news.mp3"):
    tts = gTTS(text=news_text, lang='en')
    tts.save(filename)
    logger.info(f"🎤 Generated TTS audio: {filename}")
    return filename

# ------------------------
# Function to post audio to Telegram
# ------------------------
def post_to_telegram(audio_file_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram credentials missing — skipping post")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio"
    with open(audio_file_path, "rb") as audio:
        files = {"audio": audio}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "📢 Daily AI News"}
        response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        logger.info("✅ Posted audio to Telegram successfully")
    else:
        logger.error(f"❌ Failed to post audio to Telegram: {response.text}")

# ------------------------
# Main workflow
# ------------------------
def main():
    logger.info("⏰ Running AI News workflow...")
    
    # Generate AI news text
    result = workflow.create_daily_ai_news_post()
    logger.info(f"✅ Post result: {result['status']} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Convert the news to speech
    news_text = result.get("text") or "Here are today's AI news highlights."
    audio_file = text_to_speech(news_text)
    
    # Post the audio to Telegram
    post_to_telegram(audio_file)

# ------------------------
# Run main
# ------------------------
if __name__ == "__main__":
    main()
