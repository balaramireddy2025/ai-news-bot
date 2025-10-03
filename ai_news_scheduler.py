import os
from ai_news import AINewsWorkflow
from gtts import gTTS
from moviepy.editor import *

# ------------------------
# Initialize workflow
# ------------------------
GEMINI_API_KEY = "your_gemini_api_key_here"
workflow = AINewsWorkflow(GEMINI_API_KEY)

# ------------------------
# Generate AI news
# ------------------------
result = workflow.create_daily_ai_news_post()
full_news_text = result.get("text") or "Here are today's AI news highlights."

# ------------------------
# Split into segments
# ------------------------
news_segments = [seg.strip() for seg in full_news_text.split('.') if seg.strip()]
if not news_segments:
    news_segments = [full_news_text]

video_clips = []

for i, segment in enumerate(news_segments):
    # Generate TTS audio
    audio_file = f"segment_{i}.mp3"
    tts = gTTS(text=segment, lang='en')
    tts.save(audio_file)
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration

    # Base video
    clip = ColorClip(size=(1280, 720), color=(10, 10, 50)).set_duration(duration)

    # Center text
    main_text = TextClip(segment, fontsize=50, color='white', font='Arial-Bold',
                         method='caption', size=(1100, 500))
    main_text = main_text.set_position('center').set_duration(duration)

    # Scrolling ticker
    ticker_text = TextClip(segment + " — " + segment, fontsize=30, color='yellow',
                           font='Arial-Bold', method='caption', size=(3000, 60))
    ticker = ticker_text.set_position(lambda t: (1280 - t*200, 650)).set_duration(duration)

    # Combine
    final_clip = CompositeVideoClip([clip, main_text, ticker])
    final_clip = final_clip.set_audio(audio_clip)

    video_clips.append(final_clip)

# Concatenate all segments
final_video = concatenate_videoclips(video_clips, method="compose")
final_video.write_videofile("daily_ai_news_tv.mp4", fps=24, codec="libx264")

print("✅ Your news channel style video is ready: daily_ai_news_tv.mp4")
