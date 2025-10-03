import os
import requests
from gtts import gTTS
from moviepy.editor import TextClip, CompositeVideoClip, AudioFileClip
from datetime import datetime

# --- Telegram configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("Telegram token or chat ID not set in environment variables!")

# --- AI News content ---
news_text = (
    "AI is transforming the world: sustainability, 5G-A networks, "
    "and entrepreneurship are key areas to watch."
)

# --- Convert text to speech ---
audio_file = "news.mp3"
tts = gTTS(text=news_text, lang="en")
tts.save(audio_file)

# --- Create video clip ---
# Safe for headless Linux runners (avoid ImageMagick issues)
video_width, video_height = 1280, 720
text_clip = TextClip(
    news_text,
    fontsize=40,
    color="white",
    size=(video_width, video_height),
    method="caption",  # caption method works without ImageMagick
    bg_color="black",
    align="center"
)
text_clip = text_clip.set_duration(15)

audio_clip = AudioFileClip(audio_file)
video = CompositeVideoClip([text_clip]).set_audio(audio_clip)

# --- Export MP4 ---
output_file = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")

# --- Send video to Telegram ---
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
with open(output_file, "rb") as video_file:
    response = requests.post(
        telegram_url,
        data={"chat_id": TELEGRAM_CHAT_ID},
        files={"video": video_file}
    )

if response.status_code == 200:
    print(f"✅ MP4 generated and sent to Telegram: {output_file}")
else:
    print(f"❌ Failed to send video: {response.text}")
