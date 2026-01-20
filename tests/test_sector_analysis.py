"""
Test the new sector and concept analysis functionality.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import load_config, setup_logger
from src.analyzer import ETFAnalyzer
from src.sector_data import SectorData
from src.stock_hot import StockHot
from src.notifier import Notifier

logger = setup_logger('SectorAnalysisTest')


def test_sector_analysis():
    """
    Test the sector and concept analysis pipeline.
    """
    print("=" * 60)
    print("板块和概念分析功能测试")
    print("=" * 60)

    # Initialize components
    analyzer = ETFAnalyzer()
    sector_data = SectorData()
    stock_hot = StockHot()

    # Test tweet
    fake_tweet = {
        'id': 'test_sector_001',
        'text': 'Tesla Model Y is the best-selling car in the world! Electric vehicles are the future of transportation.',
        'link': 'https://nitter.net/elonmusk/status/test_sector_001',
        'published': '2026-01-20 12:00:00'
    }

    print(f"\n[1/6] 测试推文: {fake_tweet['text']}")

    # Step 1: Get sector and concept lists
    print("\n[2/6] 获取行业和概念列表...")
    sectors_list = sector_data.get_sector_list()
    concepts_list = sector_data.get_concept_list()

    print(f"  - 行业数量: {len(sectors_list)}")
    print(f"  - 概念数量: {len(concepts_list)}")

    # Show sample sectors and concepts
    print(f"  - 示例行业: {[s.get('板块名称', s.get('name', '')) for s in sectors_list[:5]]}")
    print(f"  - 示例概念: {[c.get('板块名称', c.get('name', '')) for c in concepts_list[:5]]}")

    # Step 2: LLM analyze relevant sectors
    print("\n[3/6] LLM分析相关行业和概念...")
    relevant = analyzer.analyze_relevant_sectors(fake_tweet['text'], sectors_list, concepts_list)

    sectors = relevant.get('sectors', [])
    concepts = relevant.get('concepts', [])

    print(f"  - 相关行业: {sectors}")
    print(f"  - 相关概念: {concepts}")

    # Step 3: Get hot rank
    print("\n[4/6] 获取股票热度排名...")
    hot_rank = stock_hot.get_hot_rank()
    print(f"  - 热度股票数量: {len(hot_rank)}")

    # Show top 10 hot stocks
    sorted_hot = sorted(hot_rank.items(), key=lambda x: x[1])[:10]
    print(f"  - 热度Top 10: {[f'{code}#{rank}' for code, rank in sorted_hot[:5]]}")

    # Step 4: Get sector stocks and filter by hot
    print("\n[5/6] 获取行业成分股并过滤...")

    if sectors:
        print(f"  - 处理行业: {sectors}")
        sector_stocks = sector_data.get_multiple_sector_stocks(sectors)
        print(f"  - 行业成分股总数: {len(sector_stocks)}")

        hot_sector_stocks = stock_hot.filter_by_hot(sector_stocks, hot_rank)
        print(f"  - 热度过滤后: {len(hot_sector_stocks)}")

        if hot_sector_stocks:
            sorted_stocks = stock_hot.sort_by_hot(hot_sector_stocks)
            top_stocks = sorted_stocks[:10]

            print(f"\n  【行业热门成分股 Top {len(top_stocks)}】")
            for idx, s in enumerate(top_stocks, 1):
                print(f"    {idx}. {s['name']} ({s['code']}) - {', '.join(s['sectors'])} - 热度#{s['hot_rank']}")

    # Step 5: Get concept stocks and filter by hot
    print("\n[6/6] 获取概念成分股并过滤...")

    if concepts:
        print(f"  - 处理概念: {concepts}")
        concept_stocks = sector_data.get_multiple_concept_stocks(concepts)
        print(f"  - 概念成分股总数: {len(concept_stocks)}")

        hot_concept_stocks = stock_hot.filter_by_hot(concept_stocks, hot_rank)
        print(f"  - 热度过滤后: {len(hot_concept_stocks)}")

        if hot_concept_stocks:
            sorted_stocks = stock_hot.sort_by_hot(hot_concept_stocks)
            top_stocks = sorted_stocks[:10]

            print(f"\n  【概念热门成分股 Top {len(top_stocks)}】")
            for idx, s in enumerate(top_stocks, 1):
                print(f"    {idx}. {s['name']} ({s['code']}) - {', '.join(s['concepts'])} - 热度#{s['hot_rank']}")

    # Show notification preview
    print("\n" + "=" * 60)
    print("通知预览")
    print("=" * 60)

    config = load_config()
    notifier = Notifier(config.get('wechat_webhook_url'))

    # Build result for notifier
    analyze_result = {
        'etfs': [],
        'common_stocks': [],
        'summary': '马斯克称特斯拉Model Y成为全球最畅销车型',
        'hot_sector_stocks': stock_hot.get_top_hot(sector_stocks, 10) if sectors else [],
        'hot_concept_stocks': stock_hot.get_top_hot(concept_stocks, 10) if concepts else [],
        'sector_names': sectors,
        'concept_names': concepts
    }

    # Print notification content (without sending)
    print("\n注意: 以下为预览，不会实际发送通知\n")

    # Simulate notification content generation
    text_content = f"【马斯克推特新动态】\n\n内容：{fake_tweet['text']}\n\n链接：{fake_tweet['link']}\n时间：{fake_tweet['published']}\n"
    text_content += "--------------------------------\n"

    if analyze_result.get('summary'):
        text_content += f"💡 智能总结：{analyze_result['summary']}\n"
        text_content += "--------------------------------\n"

    hot_sector_stocks = analyze_result.get('hot_sector_stocks', [])
    hot_concept_stocks = analyze_result.get('hot_concept_stocks', [])
    sector_names = analyze_result.get('sector_names', [])
    concept_names = analyze_result.get('concept_names', [])

    if hot_sector_stocks:
        text_content += "\n【🔥 热门行业成分股 Top 10】\n"
        text_content += "（基于市场热度数据）\n\n"
        for idx, s in enumerate(hot_sector_stocks, 1):
            stock_name = s['name']
            if s['code'].startswith('300') or s['code'].startswith('301'):
                stock_name += "(创)"
            sectors_list = s.get('sectors', [])
            sectors_str = ', '.join(sectors_list[:2])
            if len(sectors_list) > 2:
                sectors_str += '...'
            text_content += f"{idx}. {stock_name} ({s['code']}) - 行业: {sectors_str} - 热度#{s['hot_rank']}\n"
    elif sector_names:
        text_content += f"\n【🔥 相关行业】\n{', '.join(sector_names)}\n"

    if hot_concept_stocks:
        text_content += "\n【🔥 热门概念成分股 Top 10】\n"
        text_content += "（基于市场热度数据）\n\n"
        for idx, s in enumerate(hot_concept_stocks, 1):
            stock_name = s['name']
            if s['code'].startswith('300') or s['code'].startswith('301'):
                stock_name += "(创)"
            concepts_list = s.get('concepts', [])
            concepts_str = ', '.join(concepts_list[:2])
            if len(concepts_list) > 2:
                concepts_str += '...'
            text_content += f"{idx}. {stock_name} ({s['code']}) - 概念: {concepts_str} - 热度#{s['hot_rank']}\n"
    elif concept_names:
        text_content += f"\n【🔥 相关概念】\n{', '.join(concept_names)}\n"

    print(text_content)

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_sector_analysis()
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n错误: {e}")
