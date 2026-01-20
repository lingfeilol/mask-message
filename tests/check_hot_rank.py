"""
Check stock_hot_rank_em actual data format.
"""

import akshare as ak

print("Testing akshare stock hot rank functions...")

# Try different functions
functions_to_test = [
    ('stock_hot_rank_em', lambda: ak.stock_hot_rank_em()),
    ('stock_zh_a_spot_em', lambda: ak.stock_zh_a_spot_em()),
]

for name, func in functions_to_test:
    print(f"\n{'=' * 60}")
    print(f"Testing: {name}")
    print(f"{'=' * 60}")
    try:
        df = func()
        print(f"✓ Success! Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"\nFirst 5 rows:")
        print(df.head(5))

        # Check for common column names
        print(f"\nChecking for '代码' column: {'代码' in df.columns}")
        print(f"Checking for '热度' related columns: {[col for col in df.columns if '热度' in col or 'hot' in col.lower()]}")

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
