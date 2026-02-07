import requests
import time
import hmac
import hashlib
import base64
import urllib.parse
from src.utils import setup_logger

logger = setup_logger('Notifier')

_UNSET = "YOUR_WECHAT_WEBHOOK_URL"


# Display name for tweet author (account handle -> 中文名)
AUTHOR_DISPLAY = {"elonmusk": "马斯克", "realDonaldTrump": "特朗普"}


def _build_message_content(tweet, analyze_result):
    """Build the same plain-text content for all channels."""
    author = tweet.get("author", "elonmusk")
    author_name = AUTHOR_DISPLAY.get(author, author)
    text_content = f"【{author_name}推特新动态】\n\n内容：{tweet['text']}\n\n链接：{tweet['link']}\n时间：{tweet['published']}\n"
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
            display_stocks = common_stocks[:10]
            text_content += f"【核心重合标的 Top {len(display_stocks)}】\n"
            text_content += "（过滤科创板及北交所）\n\n"
            for idx, s in enumerate(display_stocks):
                stock_name = s['name']
                if s['code'].startswith('300') or s['code'].startswith('301'):
                    stock_name += "(创)"
                text_content += f"{idx+1}. {stock_name} ({s['code']}) - 重合度: {s['occurrence']}/{len(etfs)}\n"
        else:
            text_content += "未发现满足过滤条件的重合持仓。"

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

    return text_content


def _send_wechat(webhook_url, text_content):
    """Send to WeChat Work bot (企业微信)."""
    if not webhook_url or webhook_url.strip() == "" or webhook_url == _UNSET:
        return False
    payload = {"msgtype": "text", "text": {"content": text_content}}
    try:
        r = requests.post(webhook_url.strip(), json=payload, timeout=10)
        r.raise_for_status()
        logger.info("WeChat notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send WeChat notification: {e}")
        return False


def _send_feishu(webhook_url, text_content, keyword=None):
    """Send to Feishu custom bot (飞书). If keyword is set, prepend it so the bot accepts the message."""
    if not webhook_url or webhook_url.strip() == "":
        return False
    content = (keyword + "\n\n" + text_content) if keyword else text_content
    payload = {"msg_type": "text", "content": {"text": content}}
    try:
        r = requests.post(webhook_url.strip(), json=payload, timeout=10)
        data = r.json()
        if data.get("code") != 0 and data.get("code") is not None:
            logger.error(f"Feishu API error: {data}")
            return False
        logger.info("Feishu notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send Feishu notification: {e}")
        return False


def _sign_dingtalk(secret):
    """DingTalk custom bot signature (timestamp + sign)."""
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = f"{timestamp}\n{secret}"
    string_to_sign_enc = string_to_sign.encode("utf-8")
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def _send_dingtalk(webhook_url, text_content, secret=None):
    """Send to DingTalk custom bot (钉钉). Optional secret for signed webhook."""
    if not webhook_url or webhook_url.strip() == "":
        return False
    url = webhook_url.strip()
    if secret and secret.strip():
        ts, sign = _sign_dingtalk(secret.strip())
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}timestamp={ts}&sign={sign}"
    payload = {"msgtype": "text", "text": {"content": text_content}}
    try:
        r = requests.post(url, json=payload, timeout=10)
        data = r.json()
        if data.get("errcode") != 0:
            logger.error(f"DingTalk API error: {data}")
            return False
        logger.info("DingTalk notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send DingTalk notification: {e}")
        return False


class Notifier:
    def __init__(self, config):
        """
        Initialize notifier from config.

        Config keys:
        - wechat_webhook_url: optional, 企业微信机器人 Webhook
        - feishu_webhook_url: optional, 飞书机器人 Webhook
        - feishu_keyword: optional, 飞书机器人关键字（消息需包含该关键字时才发送成功）
        - dingtalk_webhook_url: optional, 钉钉机器人 Webhook
        - dingtalk_secret: optional, 钉钉加签密钥（若机器人开启了加签）
        """
        self.config = config or {}
        self.wechat_url = (self.config.get("wechat_webhook_url") or "").strip()
        self.feishu_url = (self.config.get("feishu_webhook_url") or "").strip()
        self.feishu_keyword = (self.config.get("feishu_keyword") or "").strip() or None
        self.dingtalk_url = (self.config.get("dingtalk_webhook_url") or "").strip()
        self.dingtalk_secret = (self.config.get("dingtalk_secret") or "").strip() or None

        if not any([
            self.wechat_url and self.wechat_url != _UNSET,
            self.feishu_url,
            self.dingtalk_url
        ]):
            logger.warning(
                "No webhook configured (wechat_webhook_url / feishu_webhook_url / dingtalk_webhook_url). Notifications will be skipped."
            )

    def send_notification(self, tweet, analyze_result):
        """
        Send notification to all configured channels (WeChat / Feishu / DingTalk).

        Args:
            tweet: dict {text, link, published, ...}
            analyze_result: dict {
                etfs: [], common_stocks: [], summary: str,
                hot_sector_stocks: [], hot_concept_stocks: [],
                sector_names: [], concept_names: []
            }
        """
        text_content = _build_message_content(tweet, analyze_result)

        sent = False
        if self.wechat_url and self.wechat_url != _UNSET:
            if _send_wechat(self.wechat_url, text_content):
                sent = True
        if self.feishu_url:
            if _send_feishu(self.feishu_url, text_content, self.feishu_keyword):
                sent = True
        if self.dingtalk_url:
            if _send_dingtalk(self.dingtalk_url, text_content, self.dingtalk_secret):
                sent = True

        if not sent:
            logger.warning("No notification was sent (all channels failed or none configured).")
