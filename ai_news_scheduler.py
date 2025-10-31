name: Daily AI News Publisher

on:
  schedule:
    - cron: '0 9 * * *'  # Every day at 9:00 UTC
  workflow_dispatch:     # Manual trigger

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install FFmpeg
        run: sudo apt-get update && sudo apt-get install -y ffmpeg
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Daily News Publisher
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHANNEL_ID: ${{ secrets.TELEGRAM_CHANNEL_ID }}
        run: python daily_news_publisher.py
