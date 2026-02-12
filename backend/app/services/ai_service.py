import os
import akshare as ak
from openai import OpenAI
from typing import Optional

class AIService:
    @staticmethod
    def diagnose_stock(ticker: str) -> str:
        """
        生成个股诊断报告
        1. 获取个股基本面 + 历史行情
        2. 调用 LLM 生成分析报告
        """
        try:
            # 1. 获取基础数据
            stock_info = ak.stock_individual_info_em(symbol=ticker)
            name_row = stock_info[stock_info['item'] == '股票简介']
            name = name_row['value'].values[0] if not name_row.empty else ticker
            
            # 获取最近行情 (为了简单，只取最近5天)
            hist_df = ak.stock_zh_a_hist(symbol=ticker, period="daily", start_date="20240101", adjust="qfq")
            recent_data = hist_df.tail(5).to_markdown()
            
            # 2. 准备 Prompt
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
            
            # 3. 调用 LLM (如果配置了 API Key)
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            
            if api_key:
                client = OpenAI(api_key=api_key, base_url=base_url)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo", # 可配置
                    messages=[
                        {"role": "system", "content": "You are a professional financial analyst."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            else:
                return f"""
# 📉 {name} ({ticker}) AI 诊断报告 (Mock)

> **注意**: 未检测到 `OPENAI_API_KEY`，以下为模拟数据。

## 1. 走势分析
根据最近 5 个交易日的数据，该股呈现 **震荡** 走势。
- 最新收盘价: {hist_df.iloc[-1]['收盘']}
- 5日涨跌幅: ...

## 2. 风险提示
- 短期均线纠结，方向不明。
- 成交量未明显放大。

## 3. 操作建议
**观望**。等待突破信号确认。
                """
        except Exception as e:
            return f"Error generating report: {str(e)}"
