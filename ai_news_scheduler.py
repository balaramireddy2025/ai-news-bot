name: AI News Scheduler

on:
  schedule:
    - cron: "30 4 * * *"  # Every day at 04:30 UTC
  workflow_dispatch:        # Allow manual trigger

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      # 1️⃣ Checkout code
      - name: Checkout repository
        uses: actions/checkout@v3

      # 2️⃣ Setup Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"

      # 3️⃣ Install dependencies
      - name: Install dependencies
        run: |
          python3 -m pip install --upgrade pip
          pip install -r requirements.txt

      # 4️⃣ Run AI News scheduler
      - name: Run AI News Scheduler
        run: python3 ai_news_scheduler.py
