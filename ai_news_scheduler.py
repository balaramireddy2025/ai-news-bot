import os
import requests
from gtts import gTTS
from datetime import datetime

# ✅ Correct MoviePy imports for 2.1.1 (no 'editor'!)
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# AI News content (placeholder)
news_text = """
AI is transforming the world: sustainability, 5G-A networks, and entrepreneurship are key areas to watch.
"""

# Convert text to speech
tts = gTTS(text=news_text, lang="en")
audio_file = "news.mp3"
tts.save(audio_file)

# Create video clip
text_clip = TextClip(
    news_text,
    fontsize=40,
    color='white',
    size=(1280, 720),
    method='caption',
    bg_color='black'
).set_duration(15)

# Add audio
audio_clip = AudioFileClip(audio_file)
video = text_clip.set_audio(audio_clip)

# Export MP4
output_file = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
video.write_videofile(output_file, fps=24)

# Send to Telegram
with open(output_file, "rb") as f:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"video": f})

print("✅ MP4 generated and sent to Telegram")
