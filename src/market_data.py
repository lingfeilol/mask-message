"""
Market data module for ETF data using akshare with caching.
"""

import akshare as ak
import pandas as pd
from src.cache_manager import get_cache_manager
from src.utils import DATA_DIR, setup_logger
import os

logger = setup_logger('MarketData')
# Legacy cache file path
ETF_CACHE_FILE = os.path.join(DATA_DIR, 'etf_cache.csv')


class MarketData:
    def __init__(self):
        self.cache = get_cache_manager()

    def _load_or_update_cache(self):
        """
        Legacy method for backward compatibility.
        New code uses cache_manager directly.
        """
        # This is kept for compatibility but does nothing now
        pass

    def update_cache(self):
        """Legacy method - cache_manager handles this automatically."""
        # Clear ETF list cache to force refresh
        self.cache.clear_key('etf_list')

    def search_etfs(self, keywords):
        """
        Search ETFs by list of keywords.

        Args:
            keywords: List of keywords to search

        Returns:
            List of dicts: {'code': ..., 'name': ..., 'match_keyword': ...}
        """
        # Get ETF list using cache manager
        etf_df = self._get_etf_list()

        if etf_df is None or etf_df.empty:
            logger.warning("ETF data not available")
            return []

        results = []
        code_col = '代码'
        name_col = '名称'

        if code_col not in etf_df.columns or name_col not in etf_df.columns:
            logger.error(f"Unexpected columns in ETF data: {etf_df.columns}")
            return []

        for keyword in keywords:
            # Simple substring match
            matches = etf_df[etf_df[name_col].str.contains(keyword, na=False)]
            for _, row in matches.iterrows():
                results.append({
                    'code': str(row[code_col]),
                    'name': row[name_col],
                    'match_keyword': keyword
                })

        # Deduplicate by code
        unique_results = []
        seen_codes = set()
        for r in results:
            if r['code'] not in seen_codes:
                unique_results.append(r)
                seen_codes.add(r['code'])

        return unique_results

    def _get_etf_list(self):
        """Get ETF list using cache manager."""

        def fetch():
            logger.info("Fetching ETF list from AKShare...")
            try:
                df = ak.fund_etf_spot_em()
                logger.info(f"Fetched {len(df)} ETF records")
                return df
            except Exception as e:
                logger.error(f"Failed to fetch ETF list from AKShare: {e}")
                return pd.DataFrame()

        # Use cache manager
        cached = self.cache.get('etf_list', fetch, 'etf_list', 'csv')

        # Also save to legacy location for backward compatibility
        if cached is not None and not cached.empty:
            try:
                if not os.path.exists(DATA_DIR):
                    os.makedirs(DATA_DIR)
                cached.to_csv(ETF_CACHE_FILE, index=False)
            except Exception as e:
                logger.warning(f"Failed to save legacy cache: {e}")

        return cached

    def get_etf_list_for_analysis(self):
        """
        Get ETF list as a list of dicts for LLM analysis.

        Returns:
            List of dicts with 'code' and 'name' keys
            e.g., [{'code': '159123', 'name': '新能源ETF'}, ...]
        """
        etf_df = self._get_etf_list()

        if etf_df is None or etf_df.empty:
            return []

        code_col = '代码'
        name_col = '名称'

        if code_col not in etf_df.columns or name_col not in etf_df.columns:
            logger.error(f"Unexpected columns in ETF data: {etf_df.columns}")
            return []

        etf_list = []
        for _, row in etf_df.iterrows():
            etf_list.append({
                'code': str(row[code_col]),
                'name': str(row[name_col])
            })

        return etf_list

    def get_holdings(self, code):
        """
        Get all holdings for a given ETF code.

        Args:
            code: ETF code

        Returns:
            List of holding dicts with stock info
        """
        logger.info(f"Fetching holdings for ETF {code}")

        def fetch():
            try:
                if hasattr(ak, 'fund_portfolio_hold_em'):
                    try:
                        df = ak.fund_portfolio_hold_em(symbol=code)
                    except TypeError:
                        df = ak.fund_portfolio_hold_em(code)
                elif hasattr(ak, 'fund_portfolio_hold'):
                    logger.warning("fund_portfolio_hold requires date, skipping")
                    return []
                else:
                    df = ak.fund_portfolio_holdings_em(symbol=code)

                if df is None or df.empty:
                    return []

                all_holdings = df.to_dict('records')

                filtered_holdings = []
                for h in all_holdings:
                    s_code = h.get('股票代码')
                    if s_code is None or s_code == '':
                        continue

                    s_code = str(s_code)
                    # Exclude Star Market (688), Beijing (8, 4)
                    if s_code.startswith('688') or s_code.startswith('8') or s_code.startswith('4'):
                        continue
                    # Add default weight if missing
                    if '占净值比例' not in h or pd.isna(h.get('占净值比例')):
                        h['占净值比例'] = 0.0
                    filtered_holdings.append(h)

                return filtered_holdings

            except Exception as e:
                logger.error(f"Failed to fetch holdings for {code}: {e}")
                return []

        cache_key = f'etf_holdings_{code}'
        return self.cache.get(cache_key, fetch, 'etf_holdings', 'json')
