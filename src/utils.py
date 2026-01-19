from datetime import datetime, timedelta, timezone
import json
import os
import logging
import locale

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PROCESSED_TWEETS_FILE = os.path.join(DATA_DIR, 'processed_tweets.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def convert_to_beijing_time(time_str):
    """
    Convert Nitter time string (e.g. 'Jan 18, 2026 · 11:36 PM UTC') to Beijing Time string.
    """
    try:
        # Save current locale
        old_locale = locale.getlocale(locale.LC_TIME)
        try:
            # Set to C locale to parse English month names reliably
            locale.setlocale(locale.LC_TIME, 'C')
            
            # Remove the ' UTC' suffix and '· ' separator for easier parsing if needed, 
            # OR just match the format exactly.
            # Format: 'Jan 18, 2026 · 11:36 PM UTC'
            # Note: The dot is a middle dot '·', ensure we match it or clean it.
            # In Python strptime, non-ascii chars might be tricky depending on encoding.
            # Let's replace '·' with nothing or space to be safe.
            clean_str = time_str.replace('·', '').replace('UTC', '').strip()
            # New format: 'Jan 18, 2026  11:36 PM' (double space). Adjust format string.
            
            # Parse as UTC
            dt = datetime.strptime(clean_str, '%b %d, %Y  %I:%M %p')
            dt = dt.replace(tzinfo=timezone.utc)
            
            # Convert to Beijing (UTC+8)
            beijing_tz = timezone(timedelta(hours=8))
            dt_beijing = dt.astimezone(beijing_tz)
            
            return dt_beijing.strftime('%Y-%m-%d %H:%M:%S')
        finally:
            # Restore locale
            locale.setlocale(locale.LC_TIME, old_locale)
    except Exception as e:
        logger = logging.getLogger('Utils')
        logger.warning(f"Failed to parse time '{time_str}': {e}")
        return time_str

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_processed_tweets():
    if not os.path.exists(PROCESSED_TWEETS_FILE):
        return []
    with open(PROCESSED_TWEETS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_processed_tweets(tweet_ids):
    # Ensure unique and sorted
    unique_ids = sorted(list(set(tweet_ids)))
    # Keep only last 1000 to prevent infinite growth
    if len(unique_ids) > 1000:
        unique_ids = unique_ids[-1000:]
        
    with open(PROCESSED_TWEETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_ids, f, indent=2)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
