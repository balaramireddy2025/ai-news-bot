import os
import sys
import subprocess

# -----------------------------
# Quick Dependency Check
# -----------------------------
def install_package(pkg):
    """Try to pip install a package dynamically."""
    print(f"🔧 Installing missing package: {pkg} ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# Check for moviepy
try:
    from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
except ImportError:
    install_package("moviepy==1.0.3")
    from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip

# Check for requests
try:
    import requests
except ImportError:
    install_package("requests==2.31.0")
    import requests

# Check for dotenv
try:
    from dotenv import load_dotenv
except ImportError:
    install_package("python-dotenv==1.0.0")
    from dotenv import load_dotenv

# Check ffmpeg availability
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✅ ffmpeg is available")
    except Exception:
        print("⚠️ ffmpeg not found, trying to install...")
        subprocess.check_call(["sudo", "apt-get", "update"])
        subprocess.check_call(["sudo", "apt-get", "install", "-y", "ffmpeg"])

check_ffmpeg()

# -----------------------------
# Your AI News Bot Logic
# -----------------------------
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(message):
    """Send text to Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, data=payload)
    print("📨 Telegram response:", response.text)

def main():
    # Example placeholder - replace with your real news fetching/AI logic
    news_headline = "📰 Today's AI News: MoviePy now auto-installs in your bot! 🚀"
    send_message(news_headline)

if __name__ == "__main__":
    main()
