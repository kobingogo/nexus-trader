import logging
import json
from datetime import datetime
from app.models.signal import SignalRecord
from app.services.llm_provider import LLMProviderManager

logger = logging.getLogger(__name__)

class AgentLLM:
    """
    Handles LLM interactions for the Agent Brain.
    """

    @staticmethod
    def analyze_signal(signal: SignalRecord) -> str:
        """
        Analyze a critical/warning signal using LLM.
        Returns a markdown analysis string.
        """
        try:
            manager = LLMProviderManager()
            client, model_name = manager.get_client()

            if not client or not model_name:
                return "LLM not configured. Cannot perform deep analysis."

            # Construct Prompt
            prompt = f"""
            角色：资深市场分析师 (理性、敏锐)
            任务：分析监控系统生成的以下市场信号。

            [信号信息]
            - 类型: {signal.type}
            - 级别: {signal.level.upper()}
            - 消息: {signal.message}
            - 时间: {signal.timestamp}
            - 元数据: {signal.metadata_json}

            [数据字典]
            - limit_up_count: 涨停家数
            - limit_down_count: 跌停家数 !!注意区分!!
            - fried_board_count: 炸板家数
            - up_count: 上涨家数
            - down_count: 下跌家数
            - mood_index: 情绪指数

            [指令]
            1. **重要性**: 解释为什么这个信号值得关注。请准确引用数据（如涨跌停数量）。
            2. **风险提示**: 潜在的市场风险是什么？
            3. **操作建议**: 交易者应该采取什么行动？(具体点：减仓、对冲、观望或寻找机会)
            4. **格式**: 使用 Markdown 格式。
            5. **语言**: 必须使用中文回答。
            6. 字数控制在 200 字以内。
            """

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are NEXUS, a rational AI trading assistant. Always answer in Chinese."},
                    {"role": "user", "content": prompt}
                ],
                timeout=60,
            )

            content = response.choices[0].message.content
            return content

        except Exception as e:
            logger.error(f"AgentLLM analysis error: {e}")
            return f"Analysis failed: {str(e)}"
