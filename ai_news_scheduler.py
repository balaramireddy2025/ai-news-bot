import os
import requests
from gtts import gTTS
from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
from datetime import datetime

# ---------------- Telegram Config ----------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram BOT token or CHAT ID is not set in environment variables.")

# ---------------- AI News Content ----------------
news_text = """
AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch.
"""

# ---------------- Convert Text to Speech ----------------
audio_file = "news.mp3"
tts = gTTS(text=news_text, lang="en")
tts.save(audio_file)

# ---------------- Create Video Clip ----------------
# Create a TextClip with a black background
text_clip = TextClip(
    news_text,
    fontsize=40,
    color='white',
    size=(1280, 720),
    method='caption',
    bg_color='black',
    align='center'
)
text_clip = text_clip.set_duration(15)

# Load audio and attach to video
audio_clip = AudioFileClip(audio_file)
video = text_clip.set_audio(audio_clip)

# ---------------- Export MP4 ----------------
output_file = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")

# ---------------- Send to Telegram ----------------
with open(output_file, "rb") as f:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    response = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"video": f})

if response.status_code == 200:
    print("✅ MP4 generated and sent to Telegram successfully!")
else:
    print(f"❌ Failed to send video to Telegram. Status code: {response.status_code}, Response: {response.text}")
