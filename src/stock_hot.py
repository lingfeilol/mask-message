"""
Stock hot rank data fetching module using akshare with caching.
"""

import akshare as ak
from src.cache_manager import get_cache_manager
from src.utils import setup_logger

logger = setup_logger('StockHot')


class StockHot:
    """Handle stock hot rank data fetching with caching."""

    def __init__(self):
        self.cache = get_cache_manager()

    def get_hot_rank(self):
        """
        Get stock hot ranking data.

        Returns:
            Dict mapping stock code to hot rank (lower is hotter)
            e.g., {'000001': 1, '000002': 2, ...}
        """
        def fetch():
            try:
                df = ak.stock_hot_rank_em()
                # stock_hot_rank_em returns columns like: 当前排名, 代码, 股票名称, 最新价, 涨跌额, 涨跌幅
                hot_rank = {}
                for _, row in df.iterrows():
                    code = row.get('代码')
                    rank = row.get('当前排名')
                    if code and rank is not None:
                        # Remove prefix (SZ, SH) to match standard format
                        code = str(code)
                        if code.startswith('SZ') or code.startswith('SH'):
                            code = code[2:]

                        try:
                            hot_rank[code] = int(rank)
                        except (ValueError, TypeError):
                            continue

                logger.info(f"Fetched hot rank for {len(hot_rank)} stocks")
                return hot_rank
            except Exception as e:
                logger.error(f"Failed to fetch hot rank: {e}")
                return {}

        return self.cache.get('stock_hot_rank', fetch, 'stock_hot_rank', 'json')

    def filter_by_hot(self, stocks, hot_rank=None):
        """
        Filter stocks to only include those in hot rank.

        Args:
            stocks: Dict of stocks {code: {...}}
            hot_rank: Hot rank dict (optional, will fetch if not provided)

        Returns:
            List of stocks with hot rank info
        """
        if hot_rank is None:
            hot_rank = self.get_hot_rank()

        if not hot_rank:
            logger.warning("No hot rank data available, returning empty list")
            return []

        hot_stocks = []
        for code, info in stocks.items():
            if code in hot_rank:
                hot_stocks.append({
                    **info,
                    'hot_rank': hot_rank[code]
                })

        logger.info(f"Filtered {len(hot_stocks)} stocks from {len(stocks)} by hot rank")
        return hot_stocks

    def sort_by_hot(self, stocks):
        """
        Sort stocks by hot rank (lower rank = hotter).

        Args:
            stocks: List of stocks with 'hot_rank' field

        Returns:
            Sorted list of stocks
        """
        return sorted(stocks, key=lambda x: x.get('hot_rank', float('inf')))

    def get_top_hot(self, stocks, top_n=10):
        """
        Get top N stocks by hot rank.

        Args:
            stocks: Dict or list of stocks
            top_n: Number of top stocks to return

        Returns:
            List of top N stocks by hot rank
        """
        # Convert dict to list if needed
        if isinstance(stocks, dict):
            hot_stocks = self.filter_by_hot(stocks)
        else:
            hot_stocks = [s for s in stocks if 'hot_rank' in s]

        # Sort by hot rank
        sorted_stocks = self.sort_by_hot(hot_stocks)

        # Return top N
        return sorted_stocks[:top_n]
