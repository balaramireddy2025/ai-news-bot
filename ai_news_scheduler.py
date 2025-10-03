import os
import logging
from datetime import datetime
import feedparser
import schedule
import time
from gtts import gTTS
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
import requests

# -----------------------------
# CONFIGURATION
# -----------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set in GitHub secrets
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # Set in GitHub secrets

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_BG_COLOR = (30, 30, 30)  # Dark grey
TEXT_COLOR = "white"
FONT_SIZE = 50
FPS = 24
CLIP_DURATION_PER_LINE = 4  # seconds

# -----------------------------
# LOGGING
# -----------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def fetch_news_rss(url="https://news.google.com/rss/search?q=AI&hl=en-US&gl=US&ceid=US:en"):
    """Fetch news articles from RSS feed."""
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:3]:  # take top 3 articles
        title = entry.title
        summary = entry.summary
        articles.append(f"{title}\n\n{summary}")
    return articles

def generate_audio(text, filename="news.mp3"):
    """Generate TTS audio from text."""
    tts = gTTS(text=text, lang="en")
    tts.save(filename)
    return filename

def generate_video(text_lines, audio_file, output_file="news.mp4"):
    """Generate MP4 video from text lines + audio using MoviePy."""
    clips = []
    for line in text_lines:
        txt_clip = TextClip(line, fontsize=FONT_SIZE, color=TEXT_COLOR, method='caption', size=(VIDEO_WIDTH-100, VIDEO_HEIGHT-100))
        txt_clip = txt_clip.set_duration(CLIP_DURATION_PER_LINE).set_position('center')
        bg_clip = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=VIDEO_BG_COLOR).set_duration(CLIP_DURATION_PER_LINE)
        clips.append(CompositeVideoClip([bg_clip, txt_clip]))
    
    video = concatenate_videoclips(clips, method="compose")
    
    # Add audio
    audio_clip = AudioFileClip(audio_file)
    video = video.set_audio(audio_clip)
    
    # Write output
    video.write_videofile(output_file, fps=FPS)
    return output_file

def send_to_telegram(video_file):
    """Send MP4 video to Telegram channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(video_file, "rb") as f:
        files = {"video": f}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "Today's AI News"}
        response = requests.post(url, data=data, files=files)
    logging.info("Telegram response: %s", response.json())

# -----------------------------
# MAIN WORKFLOW
# -----------------------------
def run_workflow():
    logging.info("⏰ Running AI News workflow...")
    
    try:
        # 1. Fetch news
        articles = fetch_news_rss()
        logging.info("Fetched %d articles", len(articles))
        
        # 2. Prepare audio text (concatenate articles)
        audio_text = "\n\n".join(articles)
        audio_file = generate_audio(audio_text)
        logging.info("Generated audio file: %s", audio_file)
        
        # 3. Prepare video text lines (split long text into shorter lines)
        text_lines = []
        for art in articles:
            lines = art.split(". ")
            text_lines.extend(lines)
        
        # 4. Generate MP4 video
        video_file = generate_video(text_lines, audio_file)
        logging.info("Generated video file: %s", video_file)
        
        # 5. Send video to Telegram
        send_to_telegram(video_file)
        logging.info("✅ AI News workflow completed successfully!")
        
    except Exception as e:
        logging.error("❌ Error in AI News workflow: %s", e)

# -----------------------------
# SCHEDULE
# -----------------------------
if __name__ == "__main__":
    # Run immediately
    run_workflow()
    
    # Schedule daily at 4:30 UTC (10:00 AM IST)
    schedule.every().day.at("04:30").do(run_workflow)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
