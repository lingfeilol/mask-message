"""
Cache manager for akshare data requests.
Provides unified caching with configurable expiration times.
"""

import os
import json
import time
import pandas as pd
from src.utils import setup_logger

logger = setup_logger('CacheManager')


class CacheManager:
    def __init__(self, config_path='cache_config.json'):
        """
        Initialize cache manager with configuration.

        Args:
            config_path: Path to cache configuration file
        """
        self.config = self._load_config(config_path)
        self.cache_dir = self.config.get('cache_dir', 'data/cache')
        self.cache_times = self.config.get('cache_times', {})

        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")

    def _load_config(self, config_path):
        """Load cache configuration from file."""
        # Try to load from project root
        project_root = os.path.dirname(os.path.dirname(__file__))
        config_file = os.path.join(project_root, config_path)

        if not os.path.exists(config_file):
            logger.warning(f"Cache config not found at {config_file}, using defaults")
            return {
                'cache_dir': 'data/cache',
                'cache_times': {}
            }

        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_cache_file_path(self, cache_key, file_type='json'):
        """
        Get cache file path for a given key.

        Args:
            cache_key: Unique identifier for the cached data
            file_type: 'json' or 'csv'

        Returns:
            Full path to cache file
        """
        filename = f"{cache_key}.{file_type}"
        return os.path.join(self.cache_dir, filename)

    def _is_expired(self, cache_file, cache_time_key):
        """
        Check if cache file has expired.

        Args:
            cache_file: Path to cache file
            cache_time_key: Key in cache_times config

        Returns:
            True if expired or doesn't exist, False otherwise
        """
        if not os.path.exists(cache_file):
            return True

        cache_duration = self.cache_times.get(cache_time_key, 0)
        if cache_duration == 0:
            return True  # No caching configured

        file_time = os.path.getmtime(cache_file)
        return time.time() - file_time > cache_duration

    def get(self, cache_key, fetch_func, cache_time_key, file_type='json'):
        """
        Get data from cache or fetch using provided function.

        Args:
            cache_key: Unique identifier for caching
            fetch_func: Function to fetch fresh data (returns dict or DataFrame)
            cache_time_key: Key in cache_times config for expiration
            file_type: 'json' or 'csv'

        Returns:
            Cached or fresh data (dict or DataFrame)
        """
        cache_file = self._get_cache_file_path(cache_key, file_type)

        # Check if cache is valid
        if not self._is_expired(cache_file, cache_time_key):
            logger.debug(f"Loading from cache: {cache_key}")
            return self._load(cache_file, file_type)

        # Cache expired or doesn't exist, fetch fresh data
        logger.info(f"Fetching fresh data: {cache_key}")
        data = fetch_func()

        if data is not None:
            self._save(cache_file, data, file_type)
            logger.info(f"Cached data: {cache_key}")

        return data

    def _load(self, cache_file, file_type):
        """Load data from cache file."""
        try:
            if file_type == 'json':
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif file_type == 'csv':
                return pd.read_csv(cache_file, dtype=str)
        except Exception as e:
            logger.error(f"Failed to load cache {cache_file}: {e}")
            return None

    def _save(self, cache_file, data, file_type):
        """Save data to cache file."""
        try:
            if file_type == 'json':
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif file_type == 'csv':
                data.to_csv(cache_file, index=False)
        except Exception as e:
            logger.error(f"Failed to save cache {cache_file}: {e}")

    def clear_all(self):
        """Clear all cached files."""
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                os.remove(file_path)
            logger.info(f"Cleared all cache files in {self.cache_dir}")

    def clear_key(self, cache_key):
        """Clear specific cache key (both json and csv)."""
        for file_type in ['json', 'csv']:
            cache_file = self._get_cache_file_path(cache_key, file_type)
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.info(f"Cleared cache: {cache_key}.{file_type}")


# Global cache manager instance
_cache_manager = None


def get_cache_manager():
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
