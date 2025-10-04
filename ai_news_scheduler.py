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

def ensure_package(pkg, import_name=None, version=None):
    """Check and import a package, install if missing."""
    try:
        if import_name:
            __import__(import_name)
        else:
            __import__(pkg)
    except ImportError:
        dep = f"{pkg}=={version}" if version else pkg
        install_package(dep)

# Ensure dependencies
ensure_package("moviepy", "moviepy", "1.0.3")
ensure_package("requests", "requests", "2.31.0")
ensure_package("python-dotenv", "dotenv", "1.0.0")

# Now import AFTER ensuring they exist
from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
import requests
from dotenv import load_dotenv

# -----------------------------
# ffmpeg check
# -----------------------------
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✅ ffmpeg is available")
    except Exception:
        print("⚠️ ffmpeg not found, installing...")
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
    news_headline = "📰 Today's AI News: MoviePy is now auto-installed before import! 🚀"
    send_message(news_headline)

if __name__ == "__main__":
    main()
