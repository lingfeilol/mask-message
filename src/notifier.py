import requests
import json
from src.utils import setup_logger

logger = setup_logger('Notifier')

class Notifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_notification(self, tweet, analyze_result):
        """
        tweet: dict {text, link, published, ...}
        analyze_result: dict {etfs: [], common_stocks: []}
        """
        if not self.webhook_url or self.webhook_url == "YOUR_WECHAT_WEBHOOK_URL":
            logger.warning("WeChat webhook URL not configured. Skipping notification.")
            return

        text_content = f"【马斯克推特新动态】\n\n内容：{tweet['text']}\n\n链接：{tweet['link']}\n时间：{tweet['published']}\n"
        text_content += "--------------------------------\n"

        etfs = analyze_result.get('etfs', [])
        common_stocks = analyze_result.get('common_stocks', [])
        summary = analyze_result.get('summary', '')
        
        if summary:
            text_content += f"💡 智能总结：{summary}\n"
            text_content += "--------------------------------\n"

        if not etfs:
            text_content += "智能分析：未发现明显的A股ETF相关性。"
        else:
            etf_names = ", ".join([f"{e['name']}({e['code']})" for e in etfs])
            text_content += f"分析相关ETF：{etf_names}\n\n"
            
            if common_stocks:
                text_content += "【核心重合标的 Top 10】\n"
                text_content += "（过滤科创板及北交所）\n\n"
                for idx, s in enumerate(common_stocks):
                    # occurrence is the number of ETFs containing this stock
                    text_content += f"{idx+1}. {s['name']} ({s['code']}) - 重合度: {s['occurrence']}/{len(etfs)}\n"
            else:
                text_content += "未发现满足过滤条件的重合持仓。"

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
