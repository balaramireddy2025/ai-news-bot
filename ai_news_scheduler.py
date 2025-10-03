import os
import requests
from gtts import gTTS
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip, AudioFileClip

# --------------------------
# CONFIGURATION
# --------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Example AI-generated news text
NEWS_TITLE = "AI News Daily Update"
NEWS_CONTENT = (
    "Hello! This is a test AI news post. "
    "MoviePy 2.1.1 and gTTS are generating this MP4 without ImageMagick."
)

OUTPUT_MP4 = "ai_news.mp4"
TTS_FILE = "news_audio.mp3"
VIDEO_DURATION = 10  # seconds
VIDEO_SIZE = (1280, 720)
FONT_SIZE = 50

# --------------------------
# Step 1: Generate TTS Audio
# --------------------------
tts = gTTS(NEWS_CONTENT)
tts.save(TTS_FILE)

# --------------------------
# Step 2: Create Video Clip
# --------------------------
# Background color clip
bg_clip = ColorClip(size=VIDEO_SIZE, color=(30, 30, 30), duration=VIDEO_DURATION)

# Text clip (no ImageMagick required)
txt_clip = TextClip(
    f"{NEWS_TITLE}\n\n{NEWS_CONTENT}",
    fontsize=FONT_SIZE,
    color="white",
    method="caption",
    size=(VIDEO_SIZE[0] - 100, VIDEO_SIZE[1] - 100)
).set_position("center").set_duration(VIDEO_DURATION)

# Combine background and text
video = CompositeVideoClip([bg_clip, txt_clip])

# Add audio
video = video.set_audio(AudioFileClip(TTS_FILE))

# Export MP4
video.write_videofile(OUTPUT_MP4, fps=24, codec="libx264")

# --------------------------
# Step 3: Send to Telegram
# --------------------------
with open(OUTPUT_MP4, "rb") as f:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    files = {"video": f}
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": NEWS_TITLE}
    response = requests.post(url, data=data, files=files)

if response.status_code == 200:
    print("✅ Video sent to Telegram successfully!")
else:
    print("❌ Failed to send video. Response:", response.text)
