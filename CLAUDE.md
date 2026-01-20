# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Musk Tweet ETF Monitor - A Python application that monitors Elon Musk's tweets, analyzes financial relevance using LLM, finds related A-share ETFs and their holdings, and sends notifications via WeChat webhook.

## Common Commands

### Running the Application

**Development (with virtual environment):**
```bash
# Windows
start.bat

# Linux/macOS
./start.sh
```

**Direct Python execution:**
```bash
# Normal run
python -m src.main

# Dry run - check once and exit
python -m src.main --dry-run

# Send test notification
python -m src.main --test-notify
```

**Docker:**
```bash
# Build
docker build -t musk-monitor .

# Run
docker run -d --name musk-monitor \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  musk-monitor

# View logs
docker logs -f musk-monitor
```

### Testing

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_basic
```

### Installing Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## Architecture

### Module Overview

The application follows a pipeline architecture with these main components:

```
src/
├── main.py        - Entry point, orchestrates the pipeline and scheduling
├── monitor.py     - TwitterMonitor: scrapes tweets from Nitter instances using Playwright
├── analyzer.py    - ETFAnalyzer: uses LLM (OpenAI-compatible API) to analyze tweets
├── market_data.py - MarketData: queries AKShare for ETF data and holdings
├── notifier.py    - Notifier: sends formatted messages to WeChat webhook
└── utils.py       - Configuration loading, logging, data persistence
```

### Data Flow

1. **TwitterMonitor** fetches new tweets from Nitter instances (with fallback logic)
   - Uses Playwright with headless Chromium
   - Handles rate limiting by shuffling instances
   - Fetches parent tweet context for replies
   - Persists processed tweet IDs to `data/processed_tweets.json`

2. **ETFAnalyzer** analyzes tweet text via LLM
   - Returns Chinese summary and A-share ETF keywords
   - Configured via `config.json` under `llm_config`

3. **MarketData** searches ETFs and retrieves holdings
   - Caches ETF list for 24 hours in `data/etf_cache.csv`
   - Filters out STAR Market (688xxx) and Beijing Exchange (8xxxx, 4xxxx) stocks
   - Calculates intersection across top 5 matching ETFs

4. **Notifier** sends formatted WeChat messages
   - Includes tweet content, summary, matched ETFs, and top 10 common holdings

### Key Implementation Details

**Tweet Context Fetching (monitor.py:76-150):**
- Replies trigger navigation to detail page to fetch parent tweet
- Uses JavaScript evaluation to find the previous `.timeline-item` sibling
- Combines parent + reply text for LLM analysis

**ETF Holdings Aggregation (main.py:36-74):**
- Takes top 5 matching ETFs
- Ranks stocks by occurrence count across ETFs, then by total weight
- Returns top 10 common stocks after filtering

**State Management:**
- `processed_tweets.json`: tracks seen tweets (max 1000 IDs)
- `etf_cache.csv`: caches ETF list for 24 hours
- First run silently marks existing tweets as processed (no notifications)

## Configuration

`config.json` structure:
```json
{
  "nitter_instances": ["https://nitter.example.com"],
  "wechat_webhook_url": "https://qyapi.weixin.qq.com/...",
  "check_interval": 300,
  "llm_config": {
    "api_base": "https://api.deepseek.com/v1",
    "api_key": "your-api-key",
    "model": "deepseek-chat"
  }
}
```

Copy `config.example.json` to `config.json` and configure.

## Dependencies

- **playwright**: Browser automation for tweet scraping
- **feedparser**: RSS parsing (not actively used, scraping is primary method)
- **openai**: LLM API client (works with DeepSeek and other OpenAI-compatible APIs)
- **akshare**: A-share market data source
- **schedule**: Task scheduling

## Environment

- Python 3.8+
- Virtual environment recommended (venv)
- Platform-specific startup scripts (start.bat/start.sh)
