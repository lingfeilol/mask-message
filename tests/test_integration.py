"""
Integration test for the full tweet analysis pipeline.
Uses a fake tweet to test the complete workflow.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import load_config, setup_logger
from src.analyzer import ETFAnalyzer
from src.market_data import MarketData
from src.notifier import Notifier

logger = setup_logger('IntegrationTest')

def test_full_pipeline():
    """
    Test the full pipeline with a fake tweet.
    """
    print("=" * 60)
    print("马斯克推文分析流程集成测试")
    print("=" * 60)

    # Load config
    try:
        config = load_config()
        print("\n[1/5] 配置文件加载成功")
    except Exception as e:
        print(f"\n[1/5] 配置文件加载失败: {e}")
        return

    # Initialize components
    analyzer = ETFAnalyzer()
    market_data = MarketData()
    notifier = Notifier(config)
    print("[2/5] 组件初始化完成 (Analyzer, MarketData, Notifier)")

    # Fake tweets for testing
    fake_tweets = [
        {
            'id': 'test001',
            'text': 'Tesla Model Y is the best-selling car in the world! Electric vehicles are the future.',
            'link': 'https://nitter.net/elonmusk/status/test001',
            'published': '2026-01-20 12:00:00'
        },
        {
            'id': 'test002',
            'text': 'SpaceX Starship will make life multiplanetary. Mars awaits!',
            'link': 'https://nitter.net/elonmusk/status/test002',
            'published': '2026-01-20 12:05:00'
        },
        {
            'id': 'test003',
            'text': 'AI will be the most transformative technology in human history.',
            'link': 'https://nitter.net/elonmusk/status/test003',
            'published': '2026-01-20 12:10:00'
        }
    ]

    print("\n[3/5] 准备测试推文:")
    for i, tweet in enumerate(fake_tweets, 1):
        print(f"  推文{i}: {tweet['text'][:50]}...")

    # Test each fake tweet
    for idx, tweet in enumerate(fake_tweets, 1):
        print(f"\n{'=' * 60}")
        print(f"测试推文 {idx}/{len(fake_tweets)}")
        print(f"{'=' * 60}")

        # Step 1: Analyze with LLM
        print(f"\n[步骤1] LLM分析中...")
        keywords, summary = analyzer.analyze_tweet(tweet['text'])
        print(f"  - 关键词: {keywords}")
        print(f"  - 总结: {summary}")

        # Step 2: Search ETFs
        print(f"\n[步骤2] 搜索相关ETF...")
        etf_results = []
        final_common_stocks = []

        if keywords:
            etf_candidates = market_data.search_etfs(keywords)
            top_etfs = etf_candidates[:5]
            print(f"  - 找到 {len(etf_candidates)} 个相关ETF，取前5个")

            stock_stats = {}

            # Step 3: Get holdings
            print(f"\n[步骤3] 获取持仓数据...")
            for i, etf in enumerate(top_etfs, 1):
                print(f"  [{i}/{len(top_etfs)}] 获取 {etf['name']}({etf['code']}) 持仓...")
                holdings = market_data.get_holdings(etf['code'])
                etf['holdings'] = holdings
                etf_results.append(etf)
                print(f"      获得 {len(holdings)} 条持仓记录")

                # Accumulate stock stats
                for h in holdings:
                    s_code = h.get('股票代码')
                    s_name = h.get('股票名称')
                    try:
                        weight = float(h.get('占净值比例', 0))
                    except:
                        weight = 0.0

                    if s_code not in stock_stats:
                        stock_stats[s_code] = {'name': s_name, 'count': 0, 'total_weight': 0.0}

                    stock_stats[s_code]['count'] += 1
                    stock_stats[s_code]['total_weight'] += weight

            # Step 4: Rank stocks
            print(f"\n[步骤4] 计算重合持仓...")
            ranked_stocks = sorted(
                stock_stats.items(),
                key=lambda x: (x[1]['count'], x[1]['total_weight']),
                reverse=True
            )

            # Take top 10 common stocks
            for s_code, stats in ranked_stocks[:10]:
                final_common_stocks.append({
                    'code': s_code,
                    'name': stats['name'],
                    'occurrence': stats['count'],
                    'total_weight': stats['total_weight']
                })

            print(f"  - 找到 {len(final_common_stocks)} 个重合持仓")

        # Step 5: Show notification preview
        print(f"\n[步骤5] 通知预览:")
        print("-" * 60)

        text_content = f"【马斯克推特新动态】\n\n内容：{tweet['text']}\n\n链接：{tweet['link']}\n时间：{tweet['published']}\n"
        text_content += "--------------------------------\n"

        etfs = etf_results
        common_stocks = final_common_stocks
        summary_result = summary

        if summary_result:
            text_content += f"💡 智能总结：{summary_result}\n"
            text_content += "--------------------------------\n"

        if not etfs:
            text_content += "智能分析：未发现明显的A股ETF相关性。"
        else:
            etf_names = ", ".join([f"{e['name']}({e['code']})" for e in etfs])
            text_content += f"分析相关ETF：{etf_names}\n\n"

            if common_stocks:
                display_stocks = common_stocks[:10]
                text_content += f"【核心重合标的 Top {len(display_stocks)}】\n"
                text_content += "（过滤科创板及北交所）\n\n"
                for i, s in enumerate(display_stocks):
                    stock_name = s['name']
                    if s['code'].startswith('300') or s['code'].startswith('301'):
                        stock_name += "(创)"
                    text_content += f"{i+1}. {stock_name} ({s['code']}) - 重合度: {s['occurrence']}/{len(etfs)}\n"
            else:
                text_content += "未发现满足过滤条件的重合持仓。"

        print(text_content)
        print("-" * 60)

        # Ask if user wants to send real notification
        try:
            send_notification = input("\n是否发送真实企业微信通知? (y/n): ").strip().lower()
            if send_notification == 'y':
                notifier.send_notification(tweet, {
                    'etfs': etf_results,
                    'common_stocks': final_common_stocks,
                    'summary': summary
                })
                print("✓ 通知已发送")
            else:
                print("✗ 跳过发送通知")
        except EOFError:
            # Non-interactive environment, skip notification
            print("✗ 非交互式环境，跳过发送通知")

    print(f"\n{'=' * 60}")
    print("测试完成!")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    try:
        test_full_pipeline()
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n错误: {e}")
