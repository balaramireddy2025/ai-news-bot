import os
from ai_news import AINewsWorkflow
from gtts import gTTS
from moviepy.editor import *

# ------------------------
# Configuration
# ------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
OUTPUT_FILE = "daily_ai_news_tv.mp4"

# ------------------------
# Initialize AI News Workflow
# ------------------------
workflow = AINewsWorkflow(GEMINI_API_KEY)

# ------------------------
# Generate AI News
# ------------------------
print("⏰ Generating AI news...")
result = workflow.create_daily_ai_news_post()
full_news_text = result.get("generated_content").content
if not full_news_text:
    full_news_text = "Here are today's AI news highlights."

# ------------------------
# Split news into segments
# ------------------------
news_segments = [seg.strip() for seg in full_news_text.split('.') if seg.strip()]
if not news_segments:
    news_segments = [full_news_text]

video_clips = []

# ------------------------
# Create video segments
# ------------------------
for i, segment in enumerate(news_segments):
    print(f"🎤 Processing segment {i+1}/{len(news_segments)}: {segment[:60]}...")

    # Generate TTS audio
    audio_file = f"segment_{i}.mp3"
    tts = gTTS(text=segment, lang='en')
    tts.save(audio_file)
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration

    # Create base video clip
    clip = ColorClip(size=(1280, 720), color=(10, 10, 50)).set_duration(duration)

    # Center main text
    main_text = TextClip(segment, fontsize=50, color='white', font='Arial-Bold',
                         method='caption', size=(1100, 500)).set_position('center').set_duration(duration)

    # Scrolling ticker
    ticker_text = TextClip(segment + " — " + segment, fontsize=30, color='yellow',
                           font='Arial-Bold', method='caption', size=(3000, 60))
    ticker = ticker_text.set_position(lambda t: (1280 - t*200, 650)).set_duration(duration)

    # Combine clip, text, ticker, and audio
    final_clip = CompositeVideoClip([clip, main_text, ticker]).set_audio(audio_clip)
    video_clips.append(final_clip)

# ------------------------
# Concatenate all segments
# ------------------------
final_video = concatenate_videoclips(video_clips, method="compose")
final_video.write_videofile(OUTPUT_FILE, fps=24, codec="libx264")

print(f"✅ Video generated: {OUTPUT_FILE}")
