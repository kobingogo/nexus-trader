import os
import logging
import requests
from openai import OpenAI
from typing import Optional

from app.services.llm_provider import LLMProviderManager
from app.services.stock_search import get_stock_history_sina, get_stock_history_df
from app.services.stock_analysis import StockAnalysisService
import pandas as pd

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
    def stream_diagnose_stock(ticker: str):
        """
        Stream the stock diagnosis report.
        Yields:
             str: JSON string with "type" and "content"
        """
        import json
        
        try:
            yield json.dumps({"type": "status", "content": f"正在分析 {ticker}..."}) + "\n"
            
            # 1. 获取股票名称
            name = _quick_stock_name(ticker)
            yield json.dumps({"type": "status", "content": f"识别到股票：{name}，正在拉取行情..."}) + "\n"

            # 2. 获取并计算技术指标
            df = get_stock_history_df(ticker, days=80) 
            if not df.empty:
                df = StockAnalysisService.calculate_technicals(df)
                recent_df = df.tail(30).copy()
                
                # Format data table
                lines = ["| 日期 | 收盘 | MA5 | MA20 | RSI(6) | MACD | K/D/J | 成交量 |",
                         "|---|---|---|---|---|---|---|---|"]
                
                for _, row in recent_df.iterrows():
                    date = row.get('day', '')
                    close = f"{row.get('close', 0):.2f}"
                    ma5 = f"{row.get('ma5', 0):.2f}"
                    ma20 = f"{row.get('ma20', 0):.2f}"
                    rsi = f"{row.get('rsi_6', 0):.1f}"
                    macd = f"{row.get('macd', 0):.3f}"
                    kdj = f"{row.get('k', 0):.1f}/{row.get('d', 0):.1f}/{row.get('j', 0):.1f}"
                    vol = f"{row.get('volume', 0)/10000:.0f}万"
                    
                    lines.append(f"| {date} | {close} | {ma5} | {ma20} | {rsi} | {macd} | {kdj} | {vol} |")
                
                market_data_str = "\n".join(lines)
            else:
                market_data_str = "无法获取行情数据"

            yield json.dumps({"type": "status", "content": "正在获取基本面与新闻..."}) + "\n"

            # 3. 获取基本面
            fundamentals = StockAnalysisService.get_fundamentals(ticker)
            fund_str = "无法获取基本面数据"
            if fundamentals:
                pe = f"{fundamentals.get('pe_ttm', 'N/A')}"
                pb = f"{fundamentals.get('pb', 'N/A')}"
                mkt_val = fundamentals.get('market_cap', 0)
                if isinstance(mkt_val, (int, float)):
                   mkt_val = f"{mkt_val/100000000:.2f}亿"
                fund_str = f"- 市盈率(TTM): {pe}\n- 市净率: {pb}\n- 总市值: {mkt_val}"

            # 4. 获取新闻
            news = StockAnalysisService.get_stock_news(ticker)
            news_str = "无近期相关新闻"
            if news:
                news_lines = []
                for n in news[:3]: 
                    news_lines.append(f"- {n.get('date')} {n.get('title')}")
                news_str = "\n".join(news_lines)

            # 5. 准备 Prompt
            prompt = f"""
            角色：资深A股量化分析师
            任务：分析股票 {name} ({ticker})
            
            ### 1. 核心基本面
            {fund_str}
            
            ### 2. 近期量价与指标 (最近30日)
            {market_data_str}
            
            ### 3. 近期重要新闻
            {news_str}
            
            请基于以上数据，生成一份专业的诊断报告 (Markdown格式)。
            
            **要求：**
            1. **走势研判**：
               - 结合均线 (MA5/MA20) 判断趋势。
               - 结合 MACD/KDJ/RSI 指标分析买卖点和超买超卖状态。
               - 分析成交量变化。
            2. **基本面点评**：
               - 评价估值水平 (PE/PB) 和市值规模。
            3. **消息面解读**：
               - 如有新闻，简要分析其潜在影响；如无，可忽略。
            4. **操作建议**：
               - 明确给出：买入 / 增持 / 持有 / 减仓 / 卖出 / 观望。
               - 说明理由（支撑位/压力位）。
            """
            
            yield json.dumps({"type": "status", "content": "数据整合完毕，开始 AI 分析..."}) + "\n"

            # 6. 调用 LLM
            manager = LLMProviderManager()
            client, model_name = manager.get_client()

            if client and model_name:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a professional financial analyst. Output in Markdown."},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=120,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        c = chunk.choices[0].delta.content
                        yield json.dumps({"type": "chunk", "content": c}) + "\n"
                
                yield json.dumps({"type": "done", "content": ""}) + "\n"
            else:
                yield json.dumps({"type": "error", "content": "未配置 LLM，无法生成报告。"}) + "\n"

        except Exception as e:
            logger.error(f"Diagnose error for {ticker}: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    @staticmethod
    def diagnose_stock(ticker: str) -> str:
        """
        生成个股诊断报告
        1. 获取基础行情 (Sina)
        2. 计算技术指标 (MACD/KDJ/RSI)
        3. 获取基本面 (PE/PB/MarketCap)
        4. 获取新闻舆情
        5. 调用 LLM 生成分析报告
        """
        try:
            # 1. 获取股票名称
            name = _quick_stock_name(ticker)

            # 2. 获取并计算技术指标
            df = get_stock_history_df(ticker, days=80) # Fetch more for indicators
            if not df.empty:
                df = StockAnalysisService.calculate_technicals(df)
                # Keep last 30 days for prompt
                recent_df = df.tail(30).copy()
                
                # Format data for prompt
                # Columns: day, open, close, high, low, volume, ma5, ma10, ma20, macd, signal, hist, rsi_6, k, d, j
                # Create a markdown table
                lines = ["| 日期 | 收盘 | MA5 | MA20 | RSI(6) | MACD | K/D/J | 成交量 |",
                         "|---|---|---|---|---|---|---|---|"]
                
                for _, row in recent_df.iterrows():
                    date = row.get('day', '')
                    close = f"{row.get('close', 0):.2f}"
                    ma5 = f"{row.get('ma5', 0):.2f}"
                    ma20 = f"{row.get('ma20', 0):.2f}"
                    rsi = f"{row.get('rsi_6', 0):.1f}"
                    macd = f"{row.get('macd', 0):.3f}"
                    kdj = f"{row.get('k', 0):.1f}/{row.get('d', 0):.1f}/{row.get('j', 0):.1f}"
                    vol = f"{row.get('volume', 0)/10000:.0f}万"
                    
                    lines.append(f"| {date} | {close} | {ma5} | {ma20} | {rsi} | {macd} | {kdj} | {vol} |")
                
                market_data_str = "\n".join(lines)
            else:
                market_data_str = "无法获取行情数据"

            # 3. 获取基本面
            fundamentals = StockAnalysisService.get_fundamentals(ticker)
            fund_str = "无法获取基本面数据"
            if fundamentals:
                pe = f"{fundamentals.get('pe_ttm', 'N/A')}"
                pb = f"{fundamentals.get('pb', 'N/A')}"
                mkt_val = fundamentals.get('market_cap', 0)
                if isinstance(mkt_val, (int, float)):
                   mkt_val = f"{mkt_val/100000000:.2f}亿"
                fund_str = f"- 市盈率(TTM): {pe}\n- 市净率: {pb}\n- 总市值: {mkt_val}"

            # 4. 获取新闻
            news = StockAnalysisService.get_stock_news(ticker)
            news_str = "无近期相关新闻"
            if news:
                news_lines = []
                for n in news[:3]: # Top 3
                    news_lines.append(f"- {n.get('date')} {n.get('title')}")
                news_str = "\n".join(news_lines)

            # 5. 准备 Prompt
            prompt = f"""
            角色：资深A股量化分析师
            任务：分析股票 {name} ({ticker})
            
            ### 1. 核心基本面
            {fund_str}
            
            ### 2. 近期量价与指标 (最近30日)
            {market_data_str}
            
            ### 3. 近期重要新闻
            {news_str}
            
            请基于以上数据，生成一份专业的诊断报告 (Markdown格式)。
            
            **要求：**
            1. **走势研判**：
               - 结合均线 (MA5/MA20) 判断趋势。
               - 结合 MACD/KDJ/RSI 指标分析买卖点和超买超卖状态。
               - 分析成交量变化。
            2. **基本面点评**：
               - 评价估值水平 (PE/PB) 和市值规模。
            3. **消息面解读**：
               - 如有新闻，简要分析其潜在影响；如无，可忽略。
            4. **操作建议**：
               - 明确给出：买入 / 增持 / 持有 / 减仓 / 卖出 / 观望。
               - 说明理由（支撑位/压力位）。
            """

            # 6. 调用 LLM
            manager = LLMProviderManager()
            client, model_name = manager.get_client()

            if client and model_name:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a professional financial analyst. Output in Markdown."},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=120,
                )
                return response.choices[0].message.content
            else:
                return f"""
# 📉 {name} ({ticker}) AI 诊断报告 (Mock)
> 未配置 LLM，仅展示收集到的数据。

## 基本面
{fund_str}

## 新闻
{news_str}

## 技术面数据
{market_data_str}
"""
        except Exception as e:
            logger.error(f"Diagnose error for {ticker}: {e}")
            return f"Error generating report: {str(e)}"

