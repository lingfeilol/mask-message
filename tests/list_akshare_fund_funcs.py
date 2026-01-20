"""
List available akshare fund portfolio functions
"""

import akshare as ak

print("可用的基金持仓相关函数:")
print("=" * 60)

for name in dir(ak):
    if 'portfolio' in name.lower() or 'hold' in name.lower():
        print(f"  - ak.{name}")

print("\n基金相关模块:")
for name in dir(ak):
    if 'fund' in name.lower() and not name.startswith('_'):
        obj = getattr(ak, name)
        if isinstance(obj, type(lambda: None)) or isinstance(obj, type):
            print(f"  - ak.{name}")
