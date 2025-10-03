import os
import requests
from datetime import datetime
from gtts import gTTS

# Correct imports for moviepy 2.1.1
from moviepy.video.VideoClip import TextClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.audio.io.AudioFileClip import AudioFileClip

# -------------------- CONFIG --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

VIDEO_WIDTH = 720
VIDEO_HEIGHT = 480
BG_COLOR = (0, 0, 0)
TEXT_COLOR = 'white'
FONT_SIZE = 40
CLIP_DURATION = 5
OUTPUT_VIDEO = "ai_news.mp4"

# -------------------- AI NEWS POSTS --------------------
AI_NEWS_POSTS = [
    "AI is revolutionizing sustainable agriculture in India.",
    "China Mobile and Huawei demonstrate 5G-A monetization.",
    "MIT's Martin Trust Center appoints new Executive Director."
]

# -------------------- VIDEO GENERATION --------------------
def generate_video(posts, output_file):
    clips = []
    for post in posts:
        # Text clip
        txt_clip = TextClip(post, fontsize=FONT_SIZE, color=TEXT_COLOR,
                            size=(VIDEO_WIDTH, VIDEO_HEIGHT), method='caption')
        txt_clip = txt_clip.set_duration(CLIP_DURATION)

        # Background clip
        bg_clip = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=BG_COLOR,
                            duration=CLIP_DURATION)

        # Combine background + text
        clip = CompositeVideoClip([bg_clip, txt_clip.set_position('center')])
        clips.append(clip)

    # Concatenate all clips
    final_clip = concatenate_videoclips(clips, method="compose")

    # Generate audio using gTTS
    full_text = " ".join(posts)
    tts = gTTS(full_text)
    audio_file = "ai_news.mp3"
    tts.save(audio_file)

    # Attach audio
    audio_clip = AudioFileClip(audio_file)
    final_clip = final_clip.set_audio(audio_clip)

    # Export MP4
    final_clip.write_videofile(output_file, fps=24, codec="libx264")

    # Cleanup
    os.remove(audio_file)

# -------------------- SEND TO TELEGRAM --------------------
def send_to_telegram(video_file, chat_id, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    with open(video_file, 'rb') as f:
        files = {"video": f}
        data = {"chat_id": chat_id, "caption": f"AI News Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        response = requests.post(url, files=files, data=data)
    print("Telegram response:", response.json())

# -------------------- MAIN --------------------
if __name__ == "__main__":
    print("⏰ Running AI News Scheduler...")
    generate_video(AI_NEWS_POSTS, OUTPUT_VIDEO)
    print(f"✅ Video generated: {OUTPUT_VIDEO}")
    send_to_telegram(OUTPUT_VIDEO, TELEGRAM_CHAT_ID, TELEGRAM_BOT_TOKEN)
    print("✅ Video sent to Telegram successfully!")
