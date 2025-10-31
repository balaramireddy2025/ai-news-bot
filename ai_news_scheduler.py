#!/usr/bin/env python3
# ================================================================
# DAILY AI NEWS PUBLISHER - TELEGRAM BOT
# Auto-publishes AI news to Telegram with 3D backgrounds
# ================================================================

print("📦 Installing packages...")
import subprocess
import sys
import os

packages = [
    'feedparser', 'beautifulsoup4', 'google-genai', 'requests',
    'pydantic', 'pillow', 'opencv-python', 'schedule',
    'numpy', 'imageio'
]

for pkg in packages:
    try:
        __import__(pkg.replace('-', '_'))
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', pkg])

try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    print("✅ FFmpeg found")
except:
    print("⚠️ FFmpeg not found. Install with: apt-get install ffmpeg")

print("✅ Packages ready!\n")

# ================================================================
# IMPORTS
# ================================================================

import json
import time
import math
import requests
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel
import feedparser
from google import genai
import subprocess as sp
import numpy as np
import cv2

# ================================================================
# CONFIGURATION - UPDATE THESE WITH YOUR VALUES
# ================================================================

print("🔑 Loading configuration...\n")

# ⚠️ REQUIRED: Replace with your actual API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "YOUR_TELEGRAM_CHANNEL_ID")

# Settings
PUBLISH_TIME = "09:00"
ENABLE_AUDIO = bool(ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != "")
HASHTAGS = "#AI #ArtificialIntelligence #Tech #News #TechNews #Innovation #ML #MachineLearning"

# Directories
OUTPUT_DIR = "./videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"✅ Configuration loaded")
print(f"  📱 Telegram Channel: {TELEGRAM_CHANNEL_ID}")
print(f"  ⏰ Publish time: {PUBLISH_TIME}")
print(f"  🔊 Audio: {'✅' if ENABLE_AUDIO else '❌'}\n")

# News sources
NEWS_SOURCES = [
    {"name": "VentureBeat AI", "feed_url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "The Verge AI", "feed_url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "MIT Tech Review", "feed_url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "Ars Technica", "feed_url": "https://feeds.arstechnica.com/arstechnica/technology-lab"},
]

VIDEO_DIMENSIONS = (1080, 1920)
FPS = 30

# ================================================================
# DATA MODELS
# ================================================================

class NewsArticle(BaseModel):
    source_name: str
    title: str
    summary: str
    link: str
    published: datetime

class GeneratedContent(BaseModel):
    headline: str
    bullet_points: List[str]
    script: str
    post_text: str

# ================================================================
# RSS NEWS AGGREGATOR
# ================================================================

class RSSNewsAggregator:
    def __init__(self, sources: List[Dict[str, str]]):
        self.sources = sources

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text().replace("...", "").strip()

    def fetch_articles(self) -> List[NewsArticle]:
        all_articles = []
        now = datetime.now()
        time_threshold = now - timedelta(days=7)

        for source in self.sources:
            try:
                print(f"  → {source['name']}...")
                feed = feedparser.parse(source["feed_url"])

                count = 0
                for entry in feed.entries:
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])
                        else:
                            published = now

                        if published < time_threshold:
                            continue

                        article = NewsArticle(
                            source_name=source["name"],
                            title=self._clean_text(entry.title),
                            summary=self._clean_text(entry.summary if hasattr(entry, 'summary') else entry.title),
                            link=entry.link,
                            published=published
                        )
                        all_articles.append(article)
                        count += 1
                    except:
                        pass

                print(f"    ✓ {count} articles")
            except Exception as e:
                print(f"    ❌ Failed: {e}")

        unique_articles = {a.link: a for a in all_articles}
        return sorted(list(unique_articles.values()), key=lambda x: x.published, reverse=True)

# ================================================================
# GEMINI CONTENT GENERATOR
# ================================================================

class GeminiContentGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-pro"

    def generate_content(self, articles: List[NewsArticle]) -> Optional[GeneratedContent]:
        if not articles:
            return None

        article_texts = "\n---\n".join([
            f"Source: {a.source_name}\nTitle: {a.title}\nSummary: {a.summary}"
            for a in articles[:3]
        ])

        system_instruction = (
            "You are an AI News Editor creating engaging content for Telegram. "
            "Script: 60 seconds (200-240 words for 1-minute video). "
            "Post text: Include emojis, hashtags-friendly. "
            "Return valid JSON."
        )

        prompt = (
            f"Today's AI News:\n{article_texts}\n\n"
            f"Generate JSON with:\n"
            f"1. 'headline' - catchy main headline (max 8 words)\n"
            f"2. 'bullet_points' - 4-5 key points (short, punchy)\n"
            f"3. 'script' - engaging news narration (200-240 words for 60 seconds)\n"
            f"4. 'post_text' - Telegram caption (200 chars max, emoji-friendly)\n"
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  → Using {self.model_name} (attempt {attempt + 1}/{max_retries})...")
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        "system_instruction": system_instruction,
                        "response_mime_type": "application/json",
                        "response_schema": GeneratedContent,
                        "temperature": 0.7
                    }
                )

                json_data = json.loads(response.text)
                content = GeneratedContent(**json_data)
                print(f"  ✅ Content generated successfully")
                return content

            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "overloaded" in error_msg.lower():
                    print(f"  ⚠️ Attempt {attempt + 1} failed: API overloaded")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"  ⏳ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                else:
                    print(f"  ❌ Error: {e}")
                    break

        print(f"  ❌ All retries failed, using fallback content")
        return self._generate_fallback_content(articles)

    def _generate_fallback_content(self, articles: List[NewsArticle]) -> GeneratedContent:
        """Fallback content generator when API fails"""
        top_titles = [a.title for a in articles[:3]]

        return GeneratedContent(
            headline="AI News Roundup Today",
            bullet_points=[
                f"📰 {top_titles[0][:50]}..." if top_titles else "AI Developments",
                f"🤖 {top_titles[1][:50]}..." if len(top_titles) > 1 else "Tech Innovation",
                "💡 Breaking AI breakthroughs",
                "🔮 Future of technology",
            ],
            script=(
                "Welcome to today's AI news update. We're covering the latest breakthroughs "
                "in artificial intelligence and technology. From machine learning innovations to "
                "generative AI advances, stay tuned for the most impactful tech stories. "
                "Our daily coverage brings you cutting-edge developments in AI, deep learning, and automation. "
                "Subscribe to our Telegram channel for instant updates on AI news and tech trends. "
                "Don't miss out on the future of artificial intelligence!"
            ),
            post_text="🤖 Daily AI News! Check today's top stories on AI breakthroughs 📱 #AI #TechNews"
        )

# ================================================================
# ELEVENLABS AUDIO GENERATOR
# ================================================================

class ElevenLabsAudioGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"

    def generate_audio(self, script: str, output_path: str) -> bool:
        if not self.api_key:
            return False

        try:
            print(f"  → Generating audio...")

            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            data = {
                "text": script,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"  ❌ Error {response.status_code}")
                return False

            with open(output_path, 'wb') as f:
                f.write(response.content)

            print(f"  ✅ Audio ready")
            return True

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

# ================================================================
# 3D ANIMATED BACKGROUND GENERATOR
# ================================================================

class AnimatedBackgroundGenerator:
    def __init__(self, width=1080, height=1920, fps=30):
        self.width = width
        self.height = height
        self.fps = fps

    def generate_3d_background_frames(self, num_frames: int, output_dir: str) -> List[str]:
        """Generate 3D animated background frames"""
        frames = []

        print(f"  → Generating {num_frames} 3D background frames...")

        for frame_idx in range(num_frames):
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

            # Base gradient background
            for y in range(self.height):
                color_val = int(10 + (y / self.height) * 50)
                frame[y, :] = [color_val, color_val + 10, color_val + 40]

            # Animated rotating 3D particles
            self._draw_3d_particles(frame, frame_idx)

            # Neural network connections
            self._draw_neural_network(frame, frame_idx)

            # Animated data streams
            self._draw_data_streams(frame, frame_idx)

            # Save frame
            frame_path = f"{output_dir}/bg_frame_{frame_idx:04d}.png"
            cv2.imwrite(frame_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            frames.append(frame_path)

            if (frame_idx + 1) % 10 == 0:
                print(f"    ✓ {frame_idx + 1}/{num_frames}")

        return frames

    def _draw_3d_particles(self, frame, frame_idx):
        """Draw rotating 3D particles"""
        num_particles = 50

        for i in range(num_particles):
            angle = (frame_idx * 2 + i * 7.2) % 360
            radius = 100 + i * 4
            x = int(self.width / 2 + radius * math.cos(math.radians(angle)))
            y = int(self.height / 3 + radius * math.sin(math.radians(angle)) * 0.5)

            size = int(3 + 2 * math.sin(frame_idx * 0.1 + i))
            color = (0, int(150 + 100 * math.sin(angle * 0.01)), 255)

            if 0 <= x < self.width and 0 <= y < self.height:
                cv2.circle(frame, (x, y), size, color, -1)
                cv2.circle(frame, (x, y), size + 2, (0, 100, 200), 1)

    def _draw_neural_network(self, frame, frame_idx):
        """Draw animated neural network nodes and connections"""
        num_nodes = 30
        grid_cols = 5
        grid_rows = 6

        node_x = self.width // (grid_cols + 1)
        node_y = self.height // (grid_rows + 1)

        nodes = []
        for row in range(grid_rows):
            for col in range(grid_cols):
                x = (col + 1) * node_x
                y = (row + 1) * node_y
                nodes.append((x, y, row, col))

        for i, (x1, y1, r1, c1) in enumerate(nodes):
            for j, (x2, y2, r2, c2) in enumerate(nodes[i+1:]):
                distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                if distance < 300:
                    phase = (frame_idx * 2 + i + j) % 100
                    opacity = int(150 * (1 + math.sin(phase * 0.1)))
                    color = (int(opacity * 0.3), int(opacity * 0.8), 255)
                    cv2.line(frame, (x1, y1), (x2, y2), color, 1)

        for x, y, _, _ in nodes:
            size = int(4 + 2 * math.sin(frame_idx * 0.05))
            cv2.circle(frame, (x, y), size, (0, 200, 255), -1)
            cv2.circle(frame, (x, y), size + 2, (0, 150, 200), 1)

    def _draw_data_streams(self, frame, frame_idx):
        """Draw animated data streams flowing across screen"""
        num_streams = 8

        for stream_id in range(num_streams):
            y_offset = (frame_idx * 3 + stream_id * 240) % self.height
            x = int(self.width * (stream_id + 1) / (num_streams + 1))

            for segment in range(5):
                seg_y = (y_offset + segment * 50) % self.height
                opacity = int(200 * (1 - segment / 5))
                color = (int(opacity * 0.2), int(opacity * 0.6), 200)
                cv2.line(frame, (x, seg_y), (x, seg_y + 50), color, 2)

            for point in range(3):
                point_y = (y_offset + point * 100) % self.height
                cv2.circle(frame, (x, point_y), 3, (100, 200, 255), -1)

    def create_video_from_frames(self, frame_list: List[str], output_path: str, duration_sec: float):
        """Create video from frames"""
        print(f"  → Creating background video ({duration_sec}s)...")

        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(self.fps),
            '-i', f"{OUTPUT_DIR}/bg_frame_%04d.png",
            '-t', str(duration_sec),
            '-c:v', 'libx264', '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            output_path
        ]

        result = sp.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Background video created")
            return True
        else:
            print(f"  ❌ Error: {result.stderr[:200]}")
            return False

# ================================================================
# VIDEO ASSEMBLER
# ================================================================

class Video3DAssembler:
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.fps = 30
        self.bg_gen = AnimatedBackgroundGenerator(self.width, self.height, self.fps)

    def assemble_video(self, content, audio_path: str, output_name: str) -> Optional[str]:
        try:
            print(f"  → Assembling 3D video...")

            duration = self._get_audio_duration(audio_path)
            if not duration:
                print("  Error: Could not determine audio duration")
                return None

            print(f"  Audio duration: {duration:.1f}s")

            num_bg_frames = int(duration * self.fps)
            bg_frames = self.bg_gen.generate_3d_background_frames(num_bg_frames, OUTPUT_DIR)

            bg_video = f"{OUTPUT_DIR}/bg_video.mp4"
            if not self.bg_gen.create_video_from_frames(bg_frames, bg_video, duration):
                print("  ❌ Failed to create background")
                return None

            output_path = f"{OUTPUT_DIR}/{output_name}.mp4"
            if not self._add_text_overlay(bg_video, content, audio_path, output_path, duration):
                return None

            print(f"  ✅ Video created: {output_path}")

            for frame in bg_frames[:10]:
                try:
                    if os.path.exists(frame):
                        os.remove(frame)
                except:
                    pass

            return output_path

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _add_text_overlay(self, bg_video: str, content, audio_path: str, output_path: str, duration: float) -> bool:
        """Add text overlay to background video"""
        try:
            headline = content.headline.replace("'", "")
            bullets = "\n".join([f"• {b}" for b in content.bullet_points[:3]])
            bullets = bullets.replace("'", "")

            drawtext_filter = (
                f"drawtext=text='{headline}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize=60:fontcolor=white:x=(w-text_w)/2:y=300:box=1:boxcolor=black@0.5,"
                f"drawtext=text='{bullets}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                f"fontsize=40:fontcolor=white:x=100:y=800:box=1:boxcolor=black@0.3"
            )

            cmd = [
                'ffmpeg', '-y',
                '-i', bg_video,
                '-i', audio_path,
                '-filter_complex', drawtext_filter,
                '-c:v', 'libx264', '-preset', 'fast',
                '-c:a', 'aac', '-b:a', '192k',
                '-map', '0:v', '-map', '1:a',
                '-shortest',
                output_path
            ]

            result = sp.run(cmd, capture_output=True, text=True)
            return result.returncode == 0

        except Exception as e:
            print(f"  ❌ Overlay error: {e}")
            return False

    def _get_audio_duration(self, audio_path: str) -> Optional[float]:
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1',
                audio_path
            ]
            result = sp.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except:
            return None

# ================================================================
# TELEGRAM PUBLISHER
# ================================================================

class TelegramPublisher:
    def __init__(self, bot_token: str, channel_id: str):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def publish_video(self, video_path: str, caption: str) -> bool:
        """Publish video to Telegram channel"""
        if not os.path.exists(video_path):
            print(f"  ❌ Video file not found: {video_path}")
            return False

        try:
            print(f"  → Publishing to Telegram...")

            with open(video_path, 'rb') as video_file:
                files = {'video': video_file}
                data = {
                    'chat_id': self.channel_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }

                response = requests.post(
                    f"{self.api_url}/sendVideo",
                    files=files,
                    data=data,
                    timeout=120
                )

            result = response.json()

            if response.status_code == 200 and result.get('ok'):
                print(f"  ✅ Published to Telegram!")
                return True
            else:
                error = result.get('description', 'Unknown error')
                print(f"  ❌ Telegram error: {error}")
                return False

        except Exception as e:
            print(f"  ❌ Publish failed: {e}")
            return False

# ================================================================
# DAILY WORKFLOW
# ================================================================

class DailyTelegramNewsWorkflow:
    def __init__(self):
        self.aggregator = RSSNewsAggregator(NEWS_SOURCES)
        self.generator = GeminiContentGenerator(GEMINI_API_KEY)
        self.audio_gen = ElevenLabsAudioGenerator(ELEVENLABS_API_KEY)
        self.assembler = Video3DAssembler()
        self.publisher = TelegramPublisher(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
        self.last_run = None

    def generate_and_publish(self):
        print("\n" + "=" * 60)
        print(f"🚀 DAILY AI NEWS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")

        try:
            print("STEP 1: Fetching AI news\n")
            articles = self.aggregator.fetch_articles()
            if not articles:
                print("❌ No articles found\n")
                return

            print(f"✅ Found {len(articles)} articles\n")

            print("STEP 2: Generating content\n")
            content = self.generator.generate_content(articles[:5])
            if not content:
                print("❌ Generation failed\n")
                return

            print(f"✅ Headline: {content.headline}\n")

            audio_path = None
            if ENABLE_AUDIO:
                print("STEP 3: Generating audio (60 seconds)\n")
                audio_path = f"{OUTPUT_DIR}/news_audio.mp3"
                if self.audio_gen.generate_audio(content.script, audio_path):
                    print()
                else:
                    print("⚠️ Audio generation failed\n")
                    return
            else:
                print("STEP 3: Audio disabled - skipping video\n")
                return

            video_path = None
            if audio_path:
                print("STEP 4: Assembling 3D animated video\n")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_path = self.assembler.assemble_video(
                    content,
                    audio_path,
                    f"news_{timestamp}"
                )
                print()
            else:
                print("STEP 4: Skipped (no audio)\n")
                return

            if video_path:
                print("STEP 5: Publishing to Telegram\n")
                caption = f"<b>{content.headline}</b>\n\n{content.post_text}\n\n{HASHTAGS}"

                if self.publisher.publish_video(video_path, caption):
                    print()
                    self.last_run = datetime.now()
                    print("=" * 60)
                    print("✅ SUCCESS - Video published to Telegram!")
                    print("=" * 60)
                else:
                    print("❌ Failed to publish\n")
            else:
                print("❌ No video created\n")

        except Exception as e:
            print(f"❌ Workflow error: {e}")
            import traceback
            traceback.print_exc()

    def schedule_daily(self):
        """Schedule daily publication"""
        schedule.every().day.at(PUBLISH_TIME).do(self.generate_and_publish)
        print(f"⏰ Scheduled to publish daily at {PUBLISH_TIME}")

    def run_scheduler(self):
        """Run the scheduler"""
        print("\n🤖 Starting Daily Telegram AI News Bot...\n")
        self.schedule_daily()

        while True:
            schedule.run_pending()
            time.sleep(60)

# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    workflow = DailyTelegramNewsWorkflow()

    print("\n" + "=" * 60)
    print("DAILY TELEGRAM AI NEWS PUBLISHER - 3D VERSION")
    print("=" * 60)

    print("\n📋 Configuration:")
    print(f"  Channel ID: {TELEGRAM_CHANNEL_ID}")
    print(f"  Publish time: {PUBLISH_TIME}")
    print(f"  Audio enabled: {ENABLE_AUDIO}")
    print(f"  Video duration: ~60 seconds")
    print(f"  3D backgrounds: ✅ Enabled")
    print(f"  Output dir: {OUTPUT_DIR}")

    print("\n🔗 Setup Instructions:")
    print("  1. Set environment variables:")
    print("     export GEMINI_API_KEY='your_key'")
    print("     export TELEGRAM_BOT_TOKEN='your_token'")
    print("     export TELEGRAM_CHANNEL_ID='your_channel_id'")
    print("     export ELEVENLABS_API_KEY='your_elevenlabs_key' (optional)")
    print("")
    print("  2. Or update the configuration at the top of this file")

    print("\n✅ Starting Daily Scheduler...")
    print("⏰ Bot will publish at configured time daily")
    print("🔄 Press Ctrl+C to stop\n")

    workflow.run_scheduler()
