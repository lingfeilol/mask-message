"""
Test alternative akshare APIs for ETF holdings
"""

import akshare as ak
import pandas as pd

# Test failing ETF codes
test_codes = ['159208', '159241', '588760', '159381']

print("测试替代 API 获取ETF持仓\n")

for code in test_codes:
    print(f"\n{'=' * 60}")
    print(f"ETF代码: {code}")
    print(f"{'=' * 60}")

    # Try fund_hold_structure_em
    print("\n1. 尝试 fund_hold_structure_em:")
    try:
        df = ak.fund_hold_structure_em(symbol=code, year="2024")
        if df is not None and not df.empty:
            print(f"   ✓ 成功! {len(df)} 行")
            print(f"   列: {df.columns.tolist()}")
            print(df.head(2))
        else:
            print(f"   ✗ 返回空数据")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # Try fund_stock_position_lg
    print("\n2. 尝试 fund_stock_position_lg:")
    try:
        df = ak.fund_stock_position_lg(symbol=code)
        if df is not None and not df.empty:
            print(f"   ✓ 成功! {len(df)} 行")
            print(f"   列: {df.columns.tolist()}")
            print(df.head(2))
        else:
            print(f"   ✗ 返回空数据")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
