import os
import logging
import requests
from openai import OpenAI
from typing import Optional

from app.services.llm_provider import LLMProviderManager
from app.services.stock_search import get_stock_history_sina

logger = logging.getLogger(__name__)

# Lightweight Sina-based stock name lookup (no akshare dependency)
_sina_session = requests.Session()
_sina_session.trust_env = False
_sina_session.headers.update({
    "Referer": "https://finance.sina.com.cn",
    "User-Agent": "Mozilla/5.0",
})


def _quick_stock_name(code: str) -> str:
    """Get stock name from Sina quote API (fast, no akshare)."""
    code = code.strip().zfill(6)
    prefix = "sh" if code.startswith(("60", "68", "11")) else "sz"
    try:
        url = f"https://hq.sinajs.cn/list={prefix}{code}"
        r = _sina_session.get(url, timeout=5)
        if r.status_code == 200 and r.text.strip():
            # Format: var hq_str_sh000001="平安银行,11.07,...";
            parts = r.text.split('"')
            if len(parts) >= 2:
                fields = parts[1].split(",")
                if fields and fields[0]:
                    return fields[0]
    except Exception:
        pass
    return code


class AIService:
    @staticmethod
    def diagnose_stock(ticker: str) -> str:
        """
        生成个股诊断报告
        1. 使用 Sina Finance 获取历史行情（避免 EastMoney 代理问题）
        2. 调用 LLM 生成分析报告
        """
        try:
            # 1. 获取股票名称 (lightweight Sina lookup)
            name = _quick_stock_name(ticker)

            # 2. 获取最近行情 (Sina, proxy-safe)
            recent_data = get_stock_history_sina(ticker, days=30)

            # 3. 准备 Prompt
            prompt = f"""
            角色：资深A股量化分析师
            任务：分析股票 {name} ({ticker})
            
            近期行情数据：
            {recent_data}
            
            请生成一份简短的诊断报告 (Markdown格式)，包含：
            1. 走势分析 (基于数据)
            2. 风险提示
            3. 操作建议 (买入/持有/卖出)
            """

            # 4. 通过 LLMProviderManager 获取客户端
            manager = LLMProviderManager()
            client, model_name = manager.get_client()

            if client and model_name:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a professional financial analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=120,  # 120s timeout
                )
                return response.choices[0].message.content
            else:
                # Mock report when no LLM configured
                return f"""
# 📉 {name} ({ticker}) AI 诊断报告 (Mock)

> **注意**: 未配置任何 LLM 提供商，以下为模拟数据。请在「AI 模型」设置中添加提供商。

## 近期行情
{recent_data}

## 1. 走势分析
根据最近交易日数据，该股呈现 **震荡** 走势。

## 2. 风险提示
- 短期均线纠结，方向不明。
- 成交量未明显放大。

## 3. 操作建议
**观望**。等待突破信号确认。
                """
        except Exception as e:
            logger.error(f"Diagnose error for {ticker}: {e}")
            return f"Error generating report: {str(e)}"

