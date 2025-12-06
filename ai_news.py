import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
import firebase_admin
from firebase_admin import db
from apscheduler.schedulers.background import BackgroundScheduler
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load configuration
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "YOUR_CHANNEL_ID")
FIREBASE_CONFIG = {
  apiKey: "AIzaSyBEOVKrdLE7G3TnxWtCjnYIqRNcO4vXQPM",
  authDomain: "ai-news-a0483.firebaseapp.com",
  databaseURL: "https://ai-news-a0483-default-rtdb.firebaseio.com",
  projectId: "ai-news-a0483",
  storageBucket: "ai-news-a0483.firebasestorage.app",
  messagingSenderId: "227037934522",
  appId: "1:227037934522:web:af54212806891a09e46383",
  measurementId: "G-ZNZBQEL8VT"
}
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "YOUR_NEWS_API_KEY")
PUBLISH_TIME = os.getenv("PUBLISH_TIME", "09:00")

# Initialize Firebase
if not firebase_admin.get_app():
    firebase_admin.initialize_app(options={
        'databaseURL': FIREBASE_CONFIG['databaseURL']
    })

OUTPUT_DIR = Path("./news_images")
OUTPUT_DIR.mkdir(exist_ok=True)

WEBHOOK_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

print("=" * 60)
print("🎨 AI NEWS COMIC GENERATOR & WEBPAGE UPDATER")
print("=" * 60)

# ============================================================
# STEP 1: FETCH AI NEWS FROM NEWS API
# ============================================================

def fetch_ai_news(num_articles=10):
    """Fetch latest AI news from NewsAPI"""
    print("\n📰 Fetching AI news...")
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': 'artificial intelligence OR machine learning OR AI OR gpu OR nvidia OR aws OR cloud computing',
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': num_articles,
            'apiKey': NEWS_API_KEY
        }
        
        response = requests.get(url, params=params)
        articles = response.json()['articles']
        
        print(f"✅ Fetched {len(articles)} articles")
        return articles
    
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        return []

# ============================================================
# STEP 2: CATEGORIZE NEWS
# ============================================================

def categorize_news(title, description=""):
    """Categorize news into: breaking, ai, cloud, crypto"""
    text = (title + " " + description).lower()
    
    if any(word in text for word in ['nvidia', 'gpu', 'chip', 'breakthrough', 'announces']):
        return 'breaking', '🚀'
    elif any(word in text for word in ['openai', 'gpt', 'llm', 'language model', 'ai']):
        return 'ai', '🤖'
    elif any(word in text for word in ['aws', 'azure', 'cloud', 'google cloud']):
        return 'cloud', '☁️'
    elif any(word in text for word in ['bitcoin', 'crypto', 'blockchain', 'ethereum']):
        return 'crypto', '💰'
    else:
        return 'ai', '🤖'

# ============================================================
# STEP 3: CREATE COMIC-STYLE IMAGE
# ============================================================

def create_comic_news_card(title, description, category, emoji, source, date, output_path):
    """Generate comic-style news card image"""
    
    # Color schemes by category
    colors = {
        'breaking': {'bg': '#ff6b6b', 'accent': '#cc0000'},
        'ai': {'bg': '#00d4ff', 'accent': '#0088ff'},
        'cloud': {'bg': '#2ecc71', 'accent': '#27ae60'},
        'crypto': {'bg': '#f39c12', 'accent': '#e67e22'}
    }
    
    color = colors.get(category, colors['ai'])
    
    # Create image (high quality for attractive look)
    width, height = 1200, 700
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        category_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        meta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        category_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()
    
    # Draw colored background header
    draw.rectangle([(0, 0), (width, 150)], fill=color['bg'])
    
    # Draw emoji
    emoji_text = emoji
    draw.text((50, 30), emoji_text, fill='white', font=title_font)
    
    # Draw category badge
    draw.text((200, 50), f"[{category.upper()}]", fill='white', font=category_font)
    
    if category == 'breaking':
        draw.text((900, 40), "🔴 BREAKING", fill='white', font=category_font)
    
    # Draw title (with word wrapping)
    title_words = title.split()
    title_lines = []
    current_line = []
    
    for word in title_words:
        current_line.append(word)
        line = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), line, font=title_font)
        if bbox[2] > width - 100:
            if len(current_line) > 1:
                current_line.pop()
                title_lines.append(' '.join(current_line))
                current_line = [word]
        else:
            if len(title_words) == title_words.index(word) + 1:
                title_lines.append(line)
    
    y_pos = 180
    for line in title_lines[:3]:
        draw.text((50, y_pos), line, fill='#333', font=title_font)
        y_pos += 60
    
    # Draw description (truncated)
    desc_text = description[:150] + "..." if len(description) > 150 else description
    draw.text((50, y_pos + 30), desc_text, fill='#666', font=desc_font)
    
    # Draw source and date at bottom
    draw.rectangle([(0, height-80), (width, height)], fill='#f5f5f5')
    draw.text((50, height-60), f"📰 {source} | 📅 {date}", fill='#666', font=meta_font)
    
    # Draw border (comic style)
    draw.rectangle([(2, 2), (width-2, height-2)], outline='#000', width=4)
    
    # Save image
    img.save(output_path)
    print(f"  ✅ Created: {output_path}")
    
    return str(output_path)

# ============================================================
# STEP 4: UPDATE FIREBASE (for webpage)
# ============================================================

def update_firebase_news(news_articles):
    """Save all news to Firebase for webpage display"""
    print("\n💾 Updating Firebase database...")
    
    try:
        ref = db.reference('news')
        
        # Transform articles
        transformed_news = []
        for article in news_articles:
            category, emoji = categorize_news(article.get('title', ''), article.get('description', ''))
            
            news_item = {
                'id': int(time.time() * 1000),
                'title': article.get('title', 'No title'),
                'description': article.get('description', 'No description')[:200],
                'category': category,
                'emoji': emoji,
                'date': article.get('publishedAt', '')[:10],
                'source': article.get('source', {}).get('name', 'Unknown'),
                'url': article.get('url', '#'),
                'image': article.get('urlToImage', ''),
                'fetchedAt': datetime.now().isoformat()
            }
            transformed_news.append(news_item)
        
        # Save to Firebase
        ref.set(transformed_news)
        
        print(f"✅ Updated Firebase with {len(transformed_news)} articles")
        return True
    
    except Exception as e:
        print(f"❌ Firebase update error: {e}")
        return False

# ============================================================
# STEP 5: SEND TO TELEGRAM
# ============================================================

def send_to_telegram(image_path, title, source):
    """Send comic image to Telegram channel"""
    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': TELEGRAM_CHANNEL_ID,
                'caption': f"📰 {title}\n\n📝 Source: {source}\n\n#AI #News #ComicStyle",
                'parse_mode': 'HTML'
            }
            
            response = requests.post(f"{WEBHOOK_URL}/sendPhoto", files=files, data=data)
            
            if response.status_code == 200:
                print(f"  ✅ Sent to Telegram")
                return True
            else:
                print(f"  ❌ Telegram error: {response.text}")
                return False
    
    except Exception as e:
        print(f"  ❌ Error sending to Telegram: {e}")
        return False

# ============================================================
# STEP 6: MAIN DAILY JOB
# ============================================================

def daily_news_job():
    """Main job that runs every day"""
    print("\n" + "=" * 60)
    print(f"🤖 Starting Daily AI News Comic Generator")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Fetch news
    articles = fetch_ai_news(num_articles=6)
    
    if not articles:
        print("❌ No articles fetched, skipping...")
        return
    
    # 2. Update Firebase (for webpage)
    update_firebase_news(articles)
    
    # 3. Generate comics and send to Telegram
    print("\n🎨 Generating comic-style cards...")
    for idx, article in enumerate(articles[:3], 1):  # Top 3 articles
        print(f"\n📄 Processing article {idx}/3...")
        
        category, emoji = categorize_news(article['title'], article.get('description', ''))
        
        output_path = OUTPUT_DIR / f"news_{idx}_{int(time.time())}.png"
        
        # Create comic image
        create_comic_news_card(
            title=article['title'],
            description=article.get('description', 'No description'),
            category=category,
            emoji=emoji,
            source=article['source']['name'],
            date=article['publishedAt'][:10],
            output_path=str(output_path)
        )
        
        # Send to Telegram
        send_to_telegram(str(output_path), article['title'][:50], article['source']['name'])
        
        time.sleep(1)  # Rate limiting
    
    print("\n✅ Daily job completed!")

# ============================================================
# STEP 7: SCHEDULE DAILY JOB
# ============================================================

def start_scheduler():
    """Start background scheduler"""
    print("\n⏰ Starting scheduler...")
    
    scheduler = BackgroundScheduler()
    
    # Schedule job
    publish_hour, publish_minute = map(int, PUBLISH_TIME.split(':'))
    scheduler.add_job(
        daily_news_job,
        'cron',
        hour=publish_hour,
        minute=publish_minute,
        id='daily_news_job',
        name='Daily AI News Comic Generator'
    )
    
    scheduler.start()
    
    print(f"✅ Scheduler started!")
    print(f"📅 Job scheduled daily at {PUBLISH_TIME}")
    print(f"📍 Telegram Channel: {TELEGRAM_CHANNEL_ID}")
    print(f"🌐 Firebase: Updating webpage automatically")
    print("\n💡 Your webpage will auto-refresh with new comic-style news!")
    print("🔄 Press Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped")
        scheduler.shutdown()

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    # Option 1: Run once immediately (for testing)
    print("\n🧪 Running news fetch immediately for testing...")
    daily_news_job()
    
    # Option 2: Start scheduler for daily runs
    print("\n" + "=" * 60)
    start_scheduler()
