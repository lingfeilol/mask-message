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

    def analyze_relevant_sectors(self, tweet_text, sector_list, concept_list):
        """
        Analyze tweet and identify relevant sectors and concepts.

        Args:
            tweet_text: Tweet content to analyze
            sector_list: List of available sectors
            concept_list: List of available concepts

        Returns:
            Dict with 'sectors' and 'concepts' keys, each containing top 3 names
            e.g., {'sectors': ['行业1', '行业2', '行业3'], 'concepts': ['概念1', '概念2', '概念3']}
        """
        logger.info(f"Analyzing relevant sectors for tweet: {tweet_text[:50]}...")

        # Extract sector/concept names
        sector_names = [s.get('板块名称', s.get('name', '')) for s in sector_list]
        concept_names = [c.get('板块名称', c.get('name', '')) for c in concept_list]

        # Limit to avoid token overflow - take first 500 each
        sector_names_str = ', '.join(sector_names[:500])
        concept_names_str = ', '.join(concept_names[:500])

        prompt = f"""
请分析这条马斯克的推文，并从给定的行业和概念列表中找出最相关的：
"{tweet_text}"

可用行业列表：{sector_names_str}

可用概念列表：{concept_names_str}

任务：
1. 理解推文的核心内容
2. 从行业列表中选择最相关的3个行业
3. 从概念列表中选择最相关的3个概念

格式要求：请直接返回一个JSON对象，不要包含markdown格式或其他废话。
{{
    "sectors": ["行业1", "行业2", "行业3"],
    "concepts": ["概念1", "概念2", "概念3"]
}}

注意事项：
- 如果没有相关的行业，sectors返回空数组 []
- 如果没有相关的概念，concepts返回空数组 []
- 行业和概念名称必须完全匹配列表中的名称
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个精通中国A股行业和概念分类的金融分析助手。"},
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
            sectors = result.get('sectors', [])
            concepts = result.get('concepts', [])

            # Ensure they are lists
            if not isinstance(sectors, list):
                sectors = []
            if not isinstance(concepts, list):
                concepts = []

            # Limit to top 3 each
            sectors = sectors[:3]
            concepts = concepts[:3]

            logger.info(f"Extracted sectors: {sectors}, concepts: {concepts}")
            return {'sectors': sectors, 'concepts': concepts}

        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM JSON response: {content}")
            return {'sectors': [], 'concepts': []}

        except Exception as e:
            logger.error(f"LLM sector analysis failed: {e}")
            return {'sectors': [], 'concepts': []}

    def analyze_relevant_etfs(self, tweet_text, etf_list):
        """
        Analyze tweet and select the 3 most relevant ETFs from the given list.

        Args:
            tweet_text: Tweet content to analyze
            etf_list: List of available ETFs, each as a dict with 'code' and 'name' keys

        Returns:
            Tuple of (summary, etf_codes):
            - summary: Chinese summary of the tweet (string)
            - etf_codes: List of top 3 ETF codes (strings)
            e.g., ("马斯克谈论特斯拉销量创新高", ['159123', '512456', '516780'])
        """
        logger.info(f"Analyzing relevant ETFs for tweet: {tweet_text[:50]}...")

        # Format ETF list for the prompt: "代码 名称"
        etf_entries = [f"{etf['code']} {etf['name']}" for etf in etf_list]
        etf_list_str = '\n'.join(etf_entries)

        prompt = f"""
请分析这条马斯克的推文，并从给定的ETF列表中选择最相关的3个：
"{tweet_text}"

可用ETF列表（格式：代码 名称）：
{etf_list_str}

任务：
1. 理解推文的核心内容和投资指向，用简短的中文总结（不超过50字）
2. 从ETF列表中选择最相关的3个ETF
3. 返回这3个ETF的代码（不是名称）

格式要求：请直接返回一个JSON对象，不要包含markdown格式或其他废话。
{{
    "summary": "推文的中文总结",
    "etf_codes": ["代码1", "代码2", "代码3"]
}}

注意事项：
- ETF代码必须是列表中存在的代码
- 如果没有相关的ETF，etf_codes返回空数组 []，但summary仍需提供
- 只返回ETF代码，不返回名称
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个精通中国A股ETF投资和马斯克言论分析的金融助手。"},
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
            summary = result.get('summary', '')
            etf_codes = result.get('etf_codes', [])

            # Ensure types
            if not isinstance(etf_codes, list):
                etf_codes = []

            # Limit to top 3
            etf_codes = etf_codes[:3]

            logger.info(f"Summary: {summary}, Selected ETF codes: {etf_codes}")
            return summary, etf_codes

        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM JSON response: {content}")
            return "", []

        except Exception as e:
            logger.error(f"LLM ETF selection failed: {e}")
            return "", []
