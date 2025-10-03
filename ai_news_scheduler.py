import os
import logging
import schedule
import time
from datetime import datetime
from gtts import gTTS
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip, AudioFileClip
import requests

# ===================== CONFIG =====================
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 480
VIDEO_BG_COLOR = (30, 30, 30)
FONT_SIZE = 40
FONT_COLOR = "white"
FONT = "Arial-Bold"  # default font on most environments

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ===================== AI NEWS FETCH (SIMULATED) =====================
def fetch_ai_news():
    """
    Replace this with actual AI-generated news content (Google GenAI / OpenAI / Perplexity)
    """
    logging.info("Fetching AI news...")
    news = [
        {
            "title": "AI Revolutionizes Agriculture & Sustainability",
            "content": (
                "Mitti Labs is using AI to help Indian rice farmers reduce methane emissions. "
                "AI is directly contributing to sustainable farming and combating climate change."
            )
        },
        {
            "title": "5G-A Unlocks New Business Models",
            "content": (
                "China Mobile Shanghai and Huawei showcase advanced 5G-A network monetization. "
                "New revenue streams and immersive user experiences are now possible."
            )
        }
    ]
    return news

# ===================== VIDEO GENERATION =====================
def generate_video(title, content, output_file="news.mp4"):
    logging.info(f"Generating video for: {title}")

    # Combine title + content
    full_text = f"{title}\n\n{content}"

    # Generate TTS audio
    tts_file = "tts.mp3"
    tts = gTTS(text=full_text, lang="en")
    tts.save(tts_file)
    audio_clip = AudioFileClip(tts_file)
    audio_duration = audio_clip.duration

    # Create a background color clip with duration = audio duration
    bg_clip = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=VIDEO_BG_COLOR, duration=audio_duration)

    # Create text clip
    text_clip = TextClip(full_text, fontsize=FONT_SIZE, color=FONT_COLOR, font=FONT, size=(VIDEO_WIDTH-40, None), method="caption")
    text_clip = text_clip.set_position("center").set_duration(audio_duration)

    # Combine video + text + audio
    video = CompositeVideoClip([bg_clip, text_clip])
    video = video.set_audio(audio_clip)

    # Write video
    video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
    logging.info(f"Video saved as {output_file}")

    # Cleanup
    audio_clip.close()
    if os.path.exists(tts_file):
        os.remove(tts_file)

    return output_file

# ===================== TELEGRAM UPLOAD =====================
def send_to_telegram(video_path):
    logging.info(f"Sending video to Telegram: {video_path}")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(video_path, "rb") as f:
        files = {"video": f}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "🤖 AI News Update"}
        resp = requests.post(url, files=files, data=data)
    if resp.status_code == 200:
        logging.info("✅ Video sent successfully!")
    else:
        logging.error(f"❌ Failed to send video. Status code: {resp.status_code}, Response: {resp.text}")

# ===================== WORKFLOW =====================
def ai_news_workflow():
    logging.info("⏰ Running AI News workflow...")
    news_list = fetch_ai_news()
    for news_item in news_list:
        video_file = generate_video(news_item["title"], news_item["content"])
        send_to_telegram(video_file)
    logging.info("✅ Workflow completed.")

# ===================== SCHEDULER =====================
# Run every day at 9:00 AM
schedule.every().day.at("09:00").do(ai_news_workflow)

logging.info("Scheduler started. Waiting for the next run...")
while True:
    schedule.run_pending()
    time.sleep(5)
