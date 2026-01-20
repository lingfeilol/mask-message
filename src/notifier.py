import requests
import json
from src.utils import setup_logger

logger = setup_logger('Notifier')


class Notifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_notification(self, tweet, analyze_result):
        """
        Send WeChat notification with tweet analysis results.

        Args:
            tweet: dict {text, link, published, ...}
            analyze_result: dict {
                etfs: [],
                common_stocks: [],
                summary: str,
                hot_sector_stocks: [],
                hot_concept_stocks: [],
                sector_names: [],
                concept_names: []
            }
        """
        if not self.webhook_url or self.webhook_url == "YOUR_WECHAT_WEBHOOK_URL":
            logger.warning("WeChat webhook URL not configured. Skipping notification.")
            return

        text_content = f"【马斯克推特新动态】\n\n内容：{tweet['text']}\n\n链接：{tweet['link']}\n时间：{tweet['published']}\n"
        text_content += "--------------------------------\n"

        etfs = analyze_result.get('etfs', [])
        common_stocks = analyze_result.get('common_stocks', [])
        summary = analyze_result.get('summary', '')
        hot_sector_stocks = analyze_result.get('hot_sector_stocks', [])
        hot_concept_stocks = analyze_result.get('hot_concept_stocks', [])
        sector_names = analyze_result.get('sector_names', [])
        concept_names = analyze_result.get('concept_names', [])

        if summary:
            text_content += f"💡 智能总结：{summary}\n"
            text_content += "--------------------------------\n"

        if not etfs:
            text_content += "智能分析：未发现明显的A股ETF相关性。"
        else:
            etf_names = ", ".join([f"{e['name']}({e['code']})" for e in etfs])
            text_content += f"📊 分析相关ETF：{etf_names}\n\n"

            if common_stocks:
                # Limit to top 10 for display
                display_stocks = common_stocks[:10]
                text_content += f"【核心重合标的 Top {len(display_stocks)}】\n"
                text_content += "（过滤科创板及北交所）\n\n"
                for idx, s in enumerate(display_stocks):
                    # occurrence is the number of ETFs containing this stock
                    stock_name = s['name']
                    # Add (创) mark for ChiNext (300xxx, 301xxx)
                    if s['code'].startswith('300') or s['code'].startswith('301'):
                        stock_name += "(创)"
                    text_content += f"{idx+1}. {stock_name} ({s['code']}) - 重合度: {s['occurrence']}/{len(etfs)}\n"
            else:
                text_content += "未发现满足过滤条件的重合持仓。"

        # Add hot sector stocks
        if hot_sector_stocks:
            text_content += "\n【🔥 热门行业成分股 Top 10】\n"
            text_content += "（基于市场热度数据）\n\n"
            for idx, s in enumerate(hot_sector_stocks, 1):
                stock_name = s['name']
                if s['code'].startswith('300') or s['code'].startswith('301'):
                    stock_name += "(创)"
                # Show sectors this stock belongs to
                sectors_list = s.get('sectors', [])
                sectors_str = ', '.join(sectors_list[:2])  # Show max 2 sectors
                if len(sectors_list) > 2:
                    sectors_str += '...'
                text_content += f"{idx}. {stock_name} ({s['code']}) - 行业: {sectors_str} - 热度#{s['hot_rank']}\n"
        elif sector_names:
            # No hot stocks but we have sector names
            text_content += f"\n【🔥 相关行业】\n{', '.join(sector_names)}\n"

        # Add hot concept stocks
        if hot_concept_stocks:
            text_content += "\n【🔥 热门概念成分股 Top 10】\n"
            text_content += "（基于市场热度数据）\n\n"
            for idx, s in enumerate(hot_concept_stocks, 1):
                stock_name = s['name']
                if s['code'].startswith('300') or s['code'].startswith('301'):
                    stock_name += "(创)"
                # Show concepts this stock belongs to
                concepts_list = s.get('concepts', [])
                concepts_str = ', '.join(concepts_list[:2])  # Show max 2 concepts
                if len(concepts_list) > 2:
                    concepts_str += '...'
                text_content += f"{idx}. {stock_name} ({s['code']}) - 概念: {concepts_str} - 热度#{s['hot_rank']}\n"
        elif concept_names:
            # No hot stocks but we have concept names
            text_content += f"\n【🔥 相关概念】\n{', '.join(concept_names)}\n"

        payload = {

            "msgtype": "text",
            "text": {
                "content": text_content
            }
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
