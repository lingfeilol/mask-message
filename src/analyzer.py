from openai import OpenAI
import json
from src.utils import load_config, setup_logger

logger = setup_logger('ETFAnalyzer')

class ETFAnalyzer:
    def __init__(self):
        config = load_config()
        llm_conf = config.get('llm_config', {})
        self.client = OpenAI(
            base_url=llm_conf.get('api_base'),
            api_key=llm_conf.get('api_key')
        )
        self.model = llm_conf.get('model', 'gpt-3.5-turbo')

    def analyze_tweet(self, tweet_text):
        """
        Analyze tweet text and return a list of related ETF keywords.
        """
        logger.info(f"Analyzing tweet: {tweet_text[:50]}...")
        
        prompt = f"""
请分析这条马斯克的推文：
"{tweet_text}"

任务：
1. 理解推文在谈论什么（加密货币、电动车、太空探索、AI、政治、或其他）。如果是评论（Review context if available），请结合上下文分析。
2. 用简短的中文总结推文核心内容（不超过50字）。
3. 请推断如果我要在中国A股市场投资相关的ETF，应该搜索什么关键词？（3-5个最相关的中文关键词）

格式要求：请直接返回一个JSON对象，不要包含markdown格式或其他废话。
{{
    "summary": "推文的中文总结",
    "keywords": ["关键词1", "关键词2", "关键词3"]
}}

如果推文完全是闲聊或无明确投资指向，keywords返回空数组 []，但summary仍需提供。
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个精通金融投资和马斯克言论分析的助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up potential markdown code blocks
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            
            result = json.loads(content)
            keywords = result.get('keywords', [])
            summary = result.get('summary', '')
            
            if isinstance(keywords, list):
                logger.info(f"Extracted keywords: {keywords}, Summary: {summary}")
                return keywords, summary
            else:
                logger.warning(f"LLM returned unexpected keywords format: {content}")
                return [], ""
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM JSON response: {content}")
            return [], ""
                
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return [], ""
