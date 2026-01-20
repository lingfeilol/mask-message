"""
Check if any auto stocks are in hot rank.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sector_data import SectorData
from src.stock_hot import StockHot

sector_data = SectorData()
stock_hot = StockHot()

# Get sector stocks for all auto-related sectors
sectors = ['汽车整车', '汽车服务', '汽车零部件']
all_sector_stocks = {}

for sector in sectors:
    stocks = sector_data.get_multiple_sector_stocks([sector])
    all_sector_stocks.update(stocks)

print(f"汽车行业总成分股数量: {len(all_sector_stocks)}")

# Get hot rank
hot_rank = stock_hot.get_hot_rank()
print(f"热度股票数量: {len(hot_rank)}")

# Check overlap
sector_codes = set(all_sector_stocks.keys())
hot_codes = set(hot_rank.keys())
overlap = sector_codes & hot_codes

print(f"\n重叠股票数量: {len(overlap)}")

if overlap:
    print("重叠股票:")
    for code in sorted(overlap, key=lambda x: hot_rank[x]):
        print(f"  {code}: {all_sector_stocks[code]['name']} - 热度#{hot_rank[code]}")
else:
    print("\n汽车行业股票没有进入热度Top 100")
    print("\n热度榜单中的股票（前30）:")
    for i, (code, rank) in enumerate(sorted(hot_rank.items(), key=lambda x: x[1])[:30], 1):
        print(f"  {i}. {code} - 热度#{rank}")
