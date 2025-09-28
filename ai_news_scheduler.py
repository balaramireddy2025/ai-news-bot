import os
import time
import schedule
import logging
from datetime import datetime
from ai_news import AINewsWorkflow   # 👈 import your workflow class

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables (or set manually here)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8042497508")

# Initialize workflow
workflow = AINewsWorkflow(
    GEMINI_API_KEY,
    LINKEDIN_ACCESS_TOKEN,
    telegram_bot_token=TELEGRAM_BOT_TOKEN,
    telegram_chat_id=TELEGRAM_CHAT_ID
)

def job():
    logger.info("⏰ Running scheduled AI news workflow...")
    result = workflow.create_daily_ai_news_post()
    logger.info(f"✅ Post result: {result['status']} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Schedule job at 10:00 IST
schedule.every().day.at("10:00").do(job)

logger.info("📅 Scheduler started. Waiting for 10:00 IST each day...")
while True:
    schedule.run_pending()
    time.sleep(60)
