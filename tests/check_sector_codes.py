"""
Check sector stocks code format.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sector_data import SectorData
from src.stock_hot import StockHot

sector_data = SectorData()
stock_hot = StockHot()

# Get sector stocks
sector_stocks = sector_data.get_multiple_sector_stocks(['汽车整车'])
print(f"行业成分股数量: {len(sector_stocks)}")
print("\n前10只股票代码:")
for code, info in list(sector_stocks.items())[:10]:
    print(f"  {code}: {info['name']}")

# Get hot rank
hot_rank = stock_hot.get_hot_rank()
print(f"\n热度股票数量: {len(hot_rank)}")
print("\n热度前10股票代码:")
for code in sorted(hot_rank.keys(), key=lambda x: hot_rank[x])[:10]:
    print(f"  {code}")

# Check overlap
sector_codes = set(sector_stocks.keys())
hot_codes = set(hot_rank.keys())
overlap = sector_codes & hot_codes

print(f"\n重叠股票数量: {len(overlap)}")
print("重叠股票:")
for code in sorted(overlap, key=lambda x: hot_rank[x])[:10]:
    print(f"  {code}: {sector_stocks[code]['name']} - 热度#{hot_rank[code]}")
