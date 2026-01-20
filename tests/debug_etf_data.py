"""
Debug script to check actual data format for different ETFs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import akshare as ak
import pandas as pd

# Test ETF codes from different categories
test_etfs = [
    # Working ones (automotive)
    ('516390', '新能源汽车ETF'),
    ('159512', '汽车ETF'),

    # Failing ones (aerospace)
    ('159208', '航天航空ETF'),
    ('159241', '航空航天ETF天弘'),

    # Failing ones (AI)
    ('588760', '科创人工智能ETF广发'),
    ('159381', '创业板人工智能ETF华夏'),
]

for code, name in test_etfs:
    print(f"\n{'=' * 60}")
    print(f"ETF: {name} ({code})")
    print(f"{'=' * 60}")

    try:
        df = ak.fund_portfolio_hold_em(symbol=code)

        if df is None or df.empty:
            print("❌ 数据为空")
            continue

        print(f"✓ 获取数据成功: {len(df)} 行")
        print(f"列名: {df.columns.tolist()}")

        # Show first few rows
        print("\n前3行数据:")
        print(df.head(3).to_string())

        # Check if '占净值比例' column exists
        if '占净值比例' in df.columns:
            print(f"\n✓ 包含 '占净值比例' 列")
        else:
            print(f"\n❌ 不包含 '占净值比例' 列")
            # Show what columns we have
            print(f"可用列: {df.columns.tolist()}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
