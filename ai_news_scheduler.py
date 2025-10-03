import os
import re
from pathlib import Path
from ai_news import AINewsWorkflow
from gtts import gTTS
from moviepy.editor import (
    ColorClip, TextClip, AudioFileClip, 
    CompositeVideoClip, concatenate_videoclips
)

# ------------------------
# Configuration
# ------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
OUTPUT_FILE = "daily_ai_news_tv.mp4"
TEMP_DIR = Path("temp_audio")

# Video settings
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_BG_COLOR = (10, 10, 50)
FPS = 24

# Text settings
MAIN_FONT_SIZE = 48
MAIN_TEXT_COLOR = 'white'
MAIN_TEXT_WIDTH = 1100
MAIN_TEXT_HEIGHT = 500

TICKER_FONT_SIZE = 30
TICKER_COLOR = 'yellow'
TICKER_SPEED = 200
TICKER_Y_POS = 650

# Font fallback
FONT_OPTIONS = ['Arial-Bold', 'Arial', 'DejaVu-Sans-Bold', 'DejaVu-Sans']

def get_available_font():
    """Try to find an available font from the options."""
    for font in FONT_OPTIONS:
        try:
            # Test if font works
            test_clip = TextClip("Test", font=font, fontsize=10)
            test_clip.close()
            return font
        except:
            continue
    return None  # Will use default font

def smart_split_text(text, max_length=150):
    """
    Split text into segments intelligently, preserving sentence structure.
    """
    # First, split by sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    segments = []
    current_segment = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence would exceed max_length, start a new segment
        if current_segment and len(current_segment + " " + sentence) > max_length:
            segments.append(current_segment)
            current_segment = sentence
        else:
            current_segment = current_segment + " " + sentence if current_segment else sentence
    
    # Add the last segment
    if current_segment:
        segments.append(current_segment)
    
    return segments if segments else [text]

def create_segment_video(segment_text, segment_index, font):
    """Create a video clip for a single news segment."""
    audio_file = TEMP_DIR / f"segment_{segment_index}.mp3"
    
    try:
        # Generate TTS audio
        print(f"  🎤 Generating audio...")
        tts = gTTS(text=segment_text, lang='en')
        tts.save(str(audio_file))
        
        audio_clip = AudioFileClip(str(audio_file))
        duration = audio_clip.duration
        
        # Create base video clip
        clip = ColorClip(
            size=(VIDEO_WIDTH, VIDEO_HEIGHT), 
            color=VIDEO_BG_COLOR
        ).set_duration(duration)
        
        # Center main text
        main_text = TextClip(
            segment_text, 
            fontsize=MAIN_FONT_SIZE, 
            color=MAIN_TEXT_COLOR,
            font=font,
            method='caption', 
            size=(MAIN_TEXT_WIDTH, MAIN_TEXT_HEIGHT)
        ).set_position('center').set_duration(duration)
        
        # Scrolling ticker (repeat text for continuous scroll)
        ticker_text_content = segment_text + " • " + segment_text + " • " + segment_text
        ticker_text = TextClip(
            ticker_text_content, 
            fontsize=TICKER_FONT_SIZE,
            color=TICKER_COLOR,
            font=font,
            method='label'
        )
        
        # Calculate ticker width for proper scrolling
        ticker_width = ticker_text.w
        ticker = ticker_text.set_position(
            lambda t: (VIDEO_WIDTH - int(t * TICKER_SPEED) % ticker_width, TICKER_Y_POS)
        ).set_duration(duration)
        
        # Combine clip, text, ticker, and audio
        final_clip = CompositeVideoClip([clip, main_text, ticker]).set_audio(audio_clip)
        
        return final_clip
        
    except Exception as e:
        print(f"  ❌ Error creating segment {segment_index}: {e}")
        raise

def cleanup_temp_files():
    """Remove temporary audio files."""
    if TEMP_DIR.exists():
        for file in TEMP_DIR.glob("segment_*.mp3"):
            try:
                file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete {file}: {e}")
        
        # Remove directory if empty
        try:
            TEMP_DIR.rmdir()
        except:
            pass

def main():
    # Create temp directory
    TEMP_DIR.mkdir(exist_ok=True)
    
    try:
        # ------------------------
        # Initialize AI News Workflow
        # ------------------------
        print("🔧 Initializing AI News Workflow...")
        workflow = AINewsWorkflow(GEMINI_API_KEY)
        
        # ------------------------
        # Generate AI News
        # ------------------------
        print("⏰ Generating AI news...")
        result = workflow.create_daily_ai_news_post()
        full_news_text = result.get("generated_content").content
        
        if not full_news_text:
            full_news_text = "Here are today's AI news highlights."
        
        print(f"📰 Generated {len(full_news_text)} characters of news content")
        
        # ------------------------
        # Get available font
        # ------------------------
        print("🔤 Detecting available fonts...")
        font = get_available_font()
        if font:
            print(f"  ✅ Using font: {font}")
        else:
            print("  ⚠️  Using system default font")
        
        # ------------------------
        # Split news into segments
        # ------------------------
        print("✂️  Splitting news into segments...")
        news_segments = smart_split_text(full_news_text)
        print(f"  📊 Created {len(news_segments)} segments")
        
        video_clips = []
        
        # ------------------------
        # Create video segments
        # ------------------------
        for i, segment in enumerate(news_segments):
            print(f"\n🎬 Processing segment {i+1}/{len(news_segments)}:")
            print(f"  📝 Text: {segment[:80]}...")
            
            try:
                clip = create_segment_video(segment, i, font)
                video_clips.append(clip)
                print(f"  ✅ Segment {i+1} complete")
            except Exception as e:
                print(f"  ❌ Failed to create segment {i+1}: {e}")
                continue
        
        if not video_clips:
            raise Exception("No video clips were successfully created")
        
        # ------------------------
        # Concatenate all segments
        # ------------------------
        print(f"\n🎞️  Concatenating {len(video_clips)} video segments...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        print(f"💾 Writing final video to {OUTPUT_FILE}...")
        final_video.write_videofile(OUTPUT_FILE, fps=FPS, codec="libx264")
        
        # Close clips to free memory
        for clip in video_clips:
            clip.close()
        final_video.close()
        
        print(f"\n✅ Video generated successfully: {OUTPUT_FILE}")
        print(f"📊 Duration: {final_video.duration:.1f} seconds")
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        # Clean up temporary files
        print("\n🧹 Cleaning up temporary files...")
        cleanup_temp_files()

if __name__ == "__main__":
    main()
