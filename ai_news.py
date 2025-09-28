# ================================================
# AI News Automation with LinkedIn & Telegram
# ================================================

# Step 1: Install required packages
!pip install -q feedparser beautifulsoup4 schedule google-generativeai requests

# Step 2: Import libraries
import os
import json
import time
import requests
from datetime import datetime
from typing import List, Dict
import google.generativeai as genai
from dataclasses import dataclass
import logging

# Optional news packages
try:
    import feedparser
    from bs4 import BeautifulSoup
    import schedule
    NEWS_FEATURES_AVAILABLE = True
    print("✅ All packages available - Full AI News features enabled!")
except ImportError as e:
    NEWS_FEATURES_AVAILABLE = False
    print("⚠️ Missing packages for AI News features:", e)

# Step 3: Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================
# Data Classes
# ==========================
@dataclass
class NewsArticle:
    title: str
    summary: str
    url: str
    published_date: str
    source: str
    category: str = "AI"

@dataclass
class GeneratedContent:
    title: str
    content: str
    hashtags: List[str]
    best_time_to_post: str
    engagement_prediction: float

# ==========================
# AI News Aggregator
# ==========================
class AINewsAggregator:
    def __init__(self):
        if not NEWS_FEATURES_AVAILABLE:
            raise ImportError("Install feedparser, beautifulsoup4, schedule for news features")
        self.news_sources = {
            'techcrunch_ai': 'https://techcrunch.com/tag/artificial-intelligence/feed/',
            'venturebeat_ai': 'https://venturebeat.com/ai/feed/',
            'mit_news': 'https://news.mit.edu/rss/topic/artificial-intelligence2',
            'ai_news': 'https://artificialintelligence-news.com/feed/',
            'the_verge_ai': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml'
        }

    def fetch_latest_ai_news(self, max_articles=10) -> List[NewsArticle]:
        all_articles = []
        for source_name, feed_url in self.news_sources.items():
            try:
                articles = self._fetch_from_feed(feed_url, source_name, max_articles // len(self.news_sources))
                all_articles.extend(articles)
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_name}: {e}")
        all_articles.sort(key=lambda x: x.published_date, reverse=True)
        return all_articles[:max_articles]

    def _fetch_from_feed(self, feed_url, source_name, max_items):
        articles = []
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:max_items]:
            summary = self._clean_text(entry.get('summary', entry.get('description', '')))
            published_date = entry.get('published', '')
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6]).isoformat()
            article = NewsArticle(
                title=self._clean_text(entry.get('title', '')),
                summary=summary[:500],
                url=entry.get('link', ''),
                published_date=published_date,
                source=source_name
            )
            articles.append(article)
        return articles

    def _clean_text(self, text):
        if not text: return ""
        soup = BeautifulSoup(text, 'html.parser')
        return ' '.join(soup.get_text().split()).strip()

    def get_trending_topics(self, articles):
        keywords = ['GPT','LLM','ChatGPT','OpenAI','Google AI','Microsoft','Meta AI',
                    'machine learning','deep learning','neural network','automation',
                    'robotics','computer vision','natural language processing','AI ethics',
                    'generative AI','AI regulation','AI startup','AI investment']
        from collections import Counter
        topics = []
        for article in articles:
            text = f"{article.title} {article.summary}".lower()
            for keyword in keywords:
                if keyword.lower() in text:
                    topics.append(keyword)
        return [topic for topic,count in Counter(topics).most_common(5)]

# ==========================
# Gemini Content Generator
# ==========================
class GeminiContentGenerator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
        self.model = genai.GenerativeModel(self.model_name)

    def generate_news_based_content(self, news_articles: List[NewsArticle], content_style="professional") -> GeneratedContent:
        prompt = self._create_news_content_prompt(news_articles, content_style)
        response = self.model.generate_content(prompt)
        return self._parse_gemini_response(response.text)

    def _create_news_content_prompt(self, articles, style):
        news_summary = ""
        for i, article in enumerate(articles[:3],1):
            news_summary += f"{i}. {article.title}\n   Source: {article.source}\n   Summary: {article.summary[:200]}...\n\n"
        return f"""
        Based on these latest AI news articles, create an engaging LinkedIn post:
        {news_summary}
        Style: {style}, Target Audience: Business professionals and AI enthusiasts
        Include actionable insights, questions for engagement.
        JSON format:
        {{"title":"", "content":"", "hashtags":["#AI","#TechNews","#Innovation","#BusinessTech","#FutureOfWork"], "best_time_to_post":"", "engagement_prediction":0.8}}
        """

    def _parse_gemini_response(self, text):
        try:
            start = text.find('{')
            end = text.rfind('}')+1
            data = json.loads(text[start:end])
            return GeneratedContent(
                title=data.get('title',''),
                content=data.get('content',''),
                hashtags=data.get('hashtags',[]),
                best_time_to_post=data.get('best_time_to_post',''),
                engagement_prediction=data.get('engagement_prediction',0.5)
            )
        except:
            return GeneratedContent(
                title="Generated LinkedIn Post",
                content=text[:1300],
                hashtags=["#linkedin","#professional"],
                best_time_to_post="Tuesday 2:00 PM",
                engagement_prediction=0.5
            )

# ==========================
# LinkedIn Publisher (Mock)
# ==========================
class LinkedInPublisher:
    def __init__(self, access_token=None):
        self.access_token = access_token

    def publish_post(self, content: GeneratedContent, person_id="mock_id"):
        logger.info(f"Publishing post to LinkedIn: {content.title}")
        return {"success": True, "post_id": f"mock_post_{int(time.time())}", "published_at": datetime.now().isoformat()}

# ==========================
# Telegram Publisher
# ==========================
class TelegramPublisher:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, content: GeneratedContent):
        text = f"{content.title}\n\n{content.content}\n\n{' '.join(content.hashtags)}"
        payload = {"chat_id": self.chat_id, "text": text}
        response = requests.post(self.api_url, data=payload)
        if response.status_code == 200:
            return {"success": True, "message_id": response.json().get("result", {}).get("message_id")}
        else:
            return {"success": False, "error": response.json()}

# ==========================
# Analytics Tracker
# ==========================
class AnalyticsTracker:
    def __init__(self):
        self.analytics_data = []

    def track_post_performance(self, post_id: str, content: GeneratedContent) -> Dict:
        performance = {
            "post_id": post_id,
            "title": content.title,
            "published_at": datetime.now().isoformat(),
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "engagement_rate": 0.0,
            "predicted_engagement": content.engagement_prediction
        }
        self.analytics_data.append(performance)
        return performance

    def get_performance_insights(self):
        if not self.analytics_data:
            return {"message": "No data yet"}
        total_posts = len(self.analytics_data)
        avg_engagement = sum(p["engagement_rate"] for p in self.analytics_data)/total_posts
        return {
            "total_posts": total_posts,
            "average_engagement_rate": avg_engagement,
            "best_performing_post": max(self.analytics_data, key=lambda x: x["engagement_rate"]),
            "insights": "Continue posting during high-engagement times"
        }

# ==========================
# AI News Workflow with Scheduling
# ==========================
class AINewsWorkflow:
    def __init__(self, gemini_api_key, linkedin_access_token=None, telegram_bot_token=None, telegram_chat_id=None):
        self.news_aggregator = AINewsAggregator()
        self.content_generator = GeminiContentGenerator(gemini_api_key)
        self.linkedin_publisher = LinkedInPublisher(linkedin_access_token) if linkedin_access_token else None
        self.telegram_publisher = TelegramPublisher(telegram_bot_token, telegram_chat_id) if telegram_bot_token and telegram_chat_id else None
        self.analytics = AnalyticsTracker()

    def create_daily_ai_news_post(self):
        news_articles = self.news_aggregator.fetch_latest_ai_news(5)
        if not news_articles:
            return {"status":"error","message":"No news found"}
        generated_content = self.content_generator.generate_news_based_content(news_articles)
        trending_topics = self.news_aggregator.get_trending_topics(news_articles)
        result = {"status":"success","generated_content":generated_content,"trending_topics":trending_topics}

        # LinkedIn posting
        if self.linkedin_publisher:
            publish_result = self.linkedin_publisher.publish_post(generated_content)
            result["linkedin_result"] = publish_result
            self.analytics.track_post_performance(publish_result["post_id"], generated_content)

        # Telegram posting
        if self.telegram_publisher:
            telegram_result = self.telegram_publisher.send_message(generated_content)
            result["telegram_result"] = telegram_result

        return result

    def schedule_daily_posts(self):
        def job():
            logger.info("🕒 Running scheduled AI news post creation...")
            result = self.create_daily_ai_news_post()
            logger.info(f"Post creation result: {result['status']}")

        # Schedule for optimal times (customizable)
        schedule.every().day.at("09:00").do(job)
        schedule.every().day.at("14:00").do(job)
        logger.info("📅 Scheduling daily AI news posts for LinkedIn & Telegram...")

        while True:
            schedule.run_pending()
            time.sleep(60)

# ==========================
# Main Demo
# ==========================
def main_demo():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
    LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token_here")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your_chat_id_here")

    if GEMINI_API_KEY=="your_gemini_api_key_here":
        print("❌ Set GEMINI_API_KEY environment variable before running.")
        return

    workflow = AINewsWorkflow(
        GEMINI_API_KEY,
        LINKEDIN_ACCESS_TOKEN,
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID
    )

    # Run a one-time demo post
    result = workflow.create_daily_ai_news_post()
    print("Demo Result:")
    print(result)

    # Uncomment below to run continuous scheduling in Colab (blocking)
    # workflow.schedule_daily_posts()

# Execute demo
main_demo()
