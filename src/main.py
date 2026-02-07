import time
import schedule
import argparse
import sys
from src.utils import load_config, setup_logger
from src.monitor import TwitterMonitor
from src.analyzer import ETFAnalyzer
from src.market_data import MarketData
from src.sector_data import SectorData
from src.stock_hot import StockHot
from src.notifier import Notifier

logger = setup_logger('Main')


def process_sectors_and_concepts(tweet_text, sectors, concepts, sector_data, stock_hot):
    """
    Process sectors and concepts: get stocks, filter by hot rank, sort, and return top 10.

    Args:
        tweet_text: Original tweet text
        sectors: List of sector names (top 3)
        concepts: List of concept names (top 3)
        sector_data: SectorData instance
        stock_hot: StockHot instance

    Returns:
        Dict with:
        - hot_sector_stocks: List of top 10 stocks from sectors
        - hot_concept_stocks: List of top 10 stocks from concepts
        - sector_names: Original sector names (for fallback display)
        - concept_names: Original concept names (for fallback display)
    """
    result = {
        'hot_sector_stocks': [],
        'hot_concept_stocks': [],
        'sector_names': sectors,
        'concept_names': concepts
    }

    if not sectors and not concepts:
        return result

    # Get hot rank
    hot_rank = stock_hot.get_hot_rank()
    if not hot_rank:
        logger.warning("No hot rank data available, skipping sector/concept analysis")
        return result

    # Process sectors
    if sectors:
        logger.info(f"Processing sectors: {sectors}")
        sector_stocks = sector_data.get_multiple_sector_stocks(sectors)
        if sector_stocks:
            # Filter by hot rank and sort
            hot_sector_stocks = stock_hot.filter_by_hot(sector_stocks, hot_rank)
            if hot_sector_stocks:
                sorted_stocks = stock_hot.sort_by_hot(hot_sector_stocks)
                result['hot_sector_stocks'] = sorted_stocks[:10]
                logger.info(f"Found {len(result['hot_sector_stocks'])} hot sector stocks")

    # Process concepts
    if concepts:
        logger.info(f"Processing concepts: {concepts}")
        concept_stocks = sector_data.get_multiple_concept_stocks(concepts)
        if concept_stocks:
            # Filter by hot rank and sort
            hot_concept_stocks = stock_hot.filter_by_hot(concept_stocks, hot_rank)
            if hot_concept_stocks:
                sorted_stocks = stock_hot.sort_by_hot(hot_concept_stocks)
                result['hot_concept_stocks'] = sorted_stocks[:10]
                logger.info(f"Found {len(result['hot_concept_stocks'])} hot concept stocks")

    return result


def job(config, analyzer, market_data, sector_data, stock_hot, notifier):
    accounts = config.get("accounts", ["elonmusk"])
    logger.info("Checking for new tweets...")
    try:
        all_new_tweets = []
        for account in accounts:
            monitor = TwitterMonitor(account=account)
            new_tweets = monitor.fetch_tweets()
            for t in new_tweets:
                t.setdefault("author", account)
            all_new_tweets.extend(new_tweets)

        if not all_new_tweets:
            logger.info("No new tweets found.")
            return

        # Get ETF list once for all tweets
        etf_list = market_data.get_etf_list_for_analysis()
        if not etf_list:
            logger.warning("ETF list not available, skipping ETF analysis")

        for tweet in all_new_tweets:
            logger.info(f"Processing new tweet [{tweet.get('author', '?')}] {tweet['id']}")

            # 1. Analyze with LLM to get summary and ETF codes
            summary = ""
            etf_results = []
            final_common_stocks = []

            if etf_list:
                summary, etf_codes = analyzer.analyze_relevant_etfs(tweet['text'], etf_list)

                # 2. Get ETF details and holdings for selected ETFs
                if etf_codes:
                    stock_stats = {}  # {code: {'name': name, 'count': 0, 'weight': 0.0}}

                    # Build ETF results from selected codes
                    for code in etf_codes:
                        # Find ETF name from list
                        etf_info = next((e for e in etf_list if e['code'] == code), None)
                        if not etf_info:
                            logger.warning(f"ETF code {code} not found in ETF list")
                            continue

                        holdings = market_data.get_holdings(code)
                        # Only include ETFs that have valid holdings data
                        if not holdings:
                            logger.info(f"ETF {etf_info['name']}({code}) has no holdings data, skipping")
                            continue

                        etf_results.append({
                            'code': code,
                            'name': etf_info['name'],
                            'holdings': holdings
                        })

                        # Deduplicate holdings by stock code within this ETF
                        # (akshare may return multiple records for the same stock)
                        unique_holdings = {}
                        for h in holdings:
                            s_code = h.get('股票代码')
                            if s_code and s_code not in unique_holdings:
                                unique_holdings[s_code] = h

                        # Accumulate stock stats for intersection (using deduplicated holdings)
                        for h in unique_holdings.values():
                            s_code = h.get('股票代码')
                            s_name = h.get('股票名称')
                            # '占净值比例' is usually a string like "10.5" or float
                            try:
                                weight = float(h.get('占净值比例', 0))
                            except:
                                weight = 0.0

                            if s_code not in stock_stats:
                                stock_stats[s_code] = {'name': s_name, 'count': 0, 'total_weight': 0.0}

                            stock_stats[s_code]['count'] += 1
                            stock_stats[s_code]['total_weight'] += weight

                    # Rank stocks: primarily by count (intersection), secondarily by total weight
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

            # 3. Process sectors and concepts (new feature)
            sector_result = {}
            try:
                # Get sector and concept lists
                sectors_list = sector_data.get_sector_list()
                concepts_list = sector_data.get_concept_list()

                # Analyze relevant sectors/concepts
                relevant = analyzer.analyze_relevant_sectors(tweet['text'], sectors_list, concepts_list)

                # Process and get hot stocks
                sector_result = process_sectors_and_concepts(
                    tweet['text'],
                    relevant.get('sectors', []),
                    relevant.get('concepts', []),
                    sector_data,
                    stock_hot
                )
            except Exception as e:
                logger.error(f"Error in sector/concept analysis: {e}", exc_info=True)

            # 5. Notify - combine results
            notifier.send_notification(tweet, {
                'etfs': etf_results,
                'common_stocks': final_common_stocks,
                'summary': summary,
                'hot_sector_stocks': sector_result.get('hot_sector_stocks', []),
                'hot_concept_stocks': sector_result.get('hot_concept_stocks', []),
                'sector_names': sector_result.get('sector_names', []),
                'concept_names': sector_result.get('concept_names', [])
            })

    except Exception as e:
        logger.error(f"Error in job loop: {e}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(description='Musk Tweet Monitor')
    parser.add_argument('--dry-run', action='store_true', help='Run once and exit, do not save processed tweets (not fully implemented in submodules but main loop will exit)')
    parser.add_argument('--test-notify', action='store_true', help='Send a test notification and exit')
    args = parser.parse_args()

    try:
        config = load_config()
    except Exception as e:
        logger.critical(f"Config load failed: {e}")
        sys.exit(1)

    analyzer = ETFAnalyzer()
    market_data = MarketData()
    sector_data = SectorData()
    stock_hot = StockHot()
    notifier = Notifier(config)

    if args.test_notify:
        logger.info("Sending test notification...")
        notifier.send_notification({
            'text': '这是一条测试推文。Tesla to the moon!',
            'link': 'https://nitter.net/elonmusk/status/123456789',
            'published': 'Mon, 12 Jan 2026 12:00:00 GMT',
            'author': 'elonmusk'
        }, {
            'etfs': [],
            'common_stocks': [],
            'summary': '测试通知',
            'hot_sector_stocks': [],
            'hot_concept_stocks': [],
            'sector_names': [],
            'concept_names': []
        })
        return

    # If dry run, we might want to just fetch current RSS and print what we WOULD do
    if args.dry_run:
        logger.info("Dry run mode: Checking once...")
        job(config, analyzer, market_data, sector_data, stock_hot, notifier)
        return

    # Schedule
    interval = config.get('check_interval', 300)
    schedule.every(interval).seconds.do(job, config, analyzer, market_data, sector_data, stock_hot, notifier)

    logger.info(f"Monitor started. Accounts: {config.get('accounts', ['elonmusk'])}. Checking every {interval} seconds.")

    # Run once at startup
    job(config, analyzer, market_data, sector_data, stock_hot, notifier)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
