"""
Sector and concept data fetching module using akshare with caching.
"""

import akshare as ak
from src.cache_manager import get_cache_manager
from src.utils import setup_logger

logger = setup_logger('SectorData')


class SectorData:
    """Handle sector and concept data fetching with caching."""

    def __init__(self):
        self.cache = get_cache_manager()

    def get_sector_list(self):
        """
        Get list of all industry sectors.

        Returns:
            List of dicts with sector info, e.g., [{'板块名称': '...', ...}, ...]
        """
        def fetch():
            try:
                df = ak.stock_board_industry_name_em()
                return df.to_dict('records')
            except Exception as e:
                logger.error(f"Failed to fetch sector list: {e}")
                return []

        return self.cache.get('sector_list', fetch, 'sector_list', 'json')

    def get_concept_list(self):
        """
        Get list of all concept sectors.

        Returns:
            List of dicts with concept info, e.g., [{'板块名称': '...', ...}, ...]
        """
        def fetch():
            try:
                df = ak.stock_board_concept_name_em()
                return df.to_dict('records')
            except Exception as e:
                logger.error(f"Failed to fetch concept list: {e}")
                return []

        return self.cache.get('concept_list', fetch, 'concept_list', 'json')

    def get_sector_stocks(self, sector_name):
        """
        Get constituent stocks for a specific industry sector.

        Args:
            sector_name: Name of the industry sector

        Returns:
            List of dicts with stock info, e.g., [{'代码': '...', '名称': '...'}, ...]
        """
        # Sanitize sector name for filename
        safe_name = sector_name.replace('/', '_').replace('\\', '_')

        def fetch():
            try:
                df = ak.stock_board_industry_cons_em(symbol=sector_name)
                return df.to_dict('records')
            except Exception as e:
                logger.error(f"Failed to fetch stocks for sector '{sector_name}': {e}")
                return []

        cache_key = f'sector_stocks_{safe_name}'
        return self.cache.get(cache_key, fetch, 'sector_stocks', 'json')

    def get_concept_stocks(self, concept_name):
        """
        Get constituent stocks for a specific concept sector.

        Args:
            concept_name: Name of the concept sector

        Returns:
            List of dicts with stock info, e.g., [{'代码': '...', '名称': '...'}, ...]
        """
        # Sanitize concept name for filename
        safe_name = concept_name.replace('/', '_').replace('\\', '_')

        def fetch():
            try:
                df = ak.stock_board_concept_cons_em(symbol=concept_name)
                return df.to_dict('records')
            except Exception as e:
                logger.error(f"Failed to fetch stocks for concept '{concept_name}': {e}")
                return []

        cache_key = f'concept_stocks_{safe_name}'
        return self.cache.get(cache_key, fetch, 'concept_stocks', 'json')

    def get_multiple_sector_stocks(self, sector_names):
        """
        Get constituent stocks for multiple sectors and merge them.

        Args:
            sector_names: List of sector names

        Returns:
            Dict mapping stock code to stock info with sectors list
            e.g., {'000001': {'code': '000001', 'name': '...', 'sectors': [...]}, ...}
        """
        stocks = {}

        for sector_name in sector_names:
            sector_stocks = self.get_sector_stocks(sector_name)
            for stock in sector_stocks:
                code = stock.get('代码')
                name = stock.get('名称')

                if not code:
                    continue

                if code not in stocks:
                    stocks[code] = {
                        'code': code,
                        'name': name,
                        'sectors': []
                    }

                if sector_name not in stocks[code]['sectors']:
                    stocks[code]['sectors'].append(sector_name)

        return stocks

    def get_multiple_concept_stocks(self, concept_names):
        """
        Get constituent stocks for multiple concepts and merge them.

        Args:
            concept_names: List of concept names

        Returns:
            Dict mapping stock code to stock info with concepts list
            e.g., {'000001': {'code': '000001', 'name': '...', 'concepts': [...]}, ...}
        """
        stocks = {}

        for concept_name in concept_names:
            concept_stocks = self.get_concept_stocks(concept_name)
            for stock in concept_stocks:
                code = stock.get('代码')
                name = stock.get('名称')

                if not code:
                    continue

                if code not in stocks:
                    stocks[code] = {
                        'code': code,
                        'name': name,
                        'concepts': []
                    }

                if concept_name not in stocks[code]['concepts']:
                    stocks[code]['concepts'].append(concept_name)

        return stocks
