import os
import time
import json
from typing import Dict, Any, Tuple
from openai import OpenAI
from datetime import datetime
from app.services.market_data import MarketDataService


class DailyReviewService:
    @staticmethod
    def stream_review():
        """
        Stream the daily review generation (yields chunks).
        Format: NDJSON (one JSON object per line).
        
        Yields:
            str: JSON string with "type" and "content"
        """
        yield json.dumps({"type": "status", "content": "正在获取市场数据..."}) + "\n"
        
        try:
            sentiment = MarketDataService.get_market_sentiment()
            heatmap = MarketDataService.get_sector_heatmap()
            leaders = MarketDataService.get_leader_stocks()
            
            context = DailyReviewService._build_context(sentiment, heatmap, leaders)
            
            yield json.dumps({"type": "status", "content": "数据获取完成，正在生成深度分析..."}) + "\n"
            
            # Get LLM Client
            from app.services.llm_provider import LLMProviderManager
            manager = LLMProviderManager()
            client, model_name = manager.get_client()
            
            if not client:
                 yield json.dumps({"type": "error", "content": "未配置 LLM，无法流式生成复盘内容。"}) + "\n"
                 return

            # Single Master Prompt for continuous streaming
            yield json.dumps({"type": "chunk", "content": f"# 📈 NEXUS 深度复盘 ({time.strftime('%Y-%m-%d')})\n\n"}) + "\n"
            
            master_prompt = f"""
你现在是 NEXUS AI 交易系统。请基于以下【市场数据】，按顺序输出深度复盘报告。

【市场数据】
{context}

【报告要求】
请输出以下四个部分，使用 Markdown 格式，标题层级需明确，每个部分约 200-300 字：

1. ## 🏛️ 机构视角 (Institutional)
   分析基本面、宏观流动性、主流板块趋势及风格切换。风格需专业、理性。
2. ## 📊 量化视角 (Quantitative)
   分析涨跌比、赚钱效应、市场广度、资金流向异常。风格需客观、数据驱动。
3. ## ⚡ 游资视角 (Hot Money)
   分析题材博弈、连板高度、情绪周期（连板、反包、核按钮等）。风格需犀利、专业游资术语丰富。
4. ## 🏁 首席回顾 (CIO Summary)
   汇总以上视角，给出【市场定调】、【核心策略】（建议仓位）及【明日重点】。风格需权威、果断。

请直接开始输出报告内容，不要有任何多余的开场白或结束语。
"""

            try:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一个顶级金融分析助手，擅长多维度视角切入分析股市。"},
                        {"role": "user", "content": master_prompt}
                    ],
                    temperature=0.7,
                    stream=True
                )
                
                for chunk in stream:
                    if hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
                        c = chunk.choices[0].delta.content
                        yield json.dumps({"type": "chunk", "content": c}) + "\n"
                
                yield json.dumps({"type": "chunk", "content": "\n\n---\n*NEXUS AI · 深度复盘系统*" }) + "\n"
                yield json.dumps({"type": "done", "content": ""}) + "\n"
                
            except Exception as e:
                error_msg = f"(流式解析过程出错: {str(e)})"
                yield json.dumps({"type": "error", "content": error_msg}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "content": f"系统故障: {str(e)}"}) + "\n"

    @staticmethod
    def _build_context(sentiment, heatmap, leaders) -> str:
        """Helper to build market context string for LLM."""
        top_sectors = heatmap[:5] if heatmap else []
        bottom_sectors = sorted(heatmap, key=lambda x: x.get("change_pct", 0))[:3] if heatmap else []
        top_leaders = leaders[:5] if leaders else []

        context_lines = [
            "## 今日市场数据摘要",
            f"- 上涨家数: {sentiment.get('up_count', 'N/A')}",
            f"- 下跌家数: {sentiment.get('down_count', 'N/A')}",
            f"- 涨停: {sentiment.get('limit_up_count', 'N/A')}",
            f"- 跌停: {sentiment.get('limit_down_count', 'N/A')}",
            f"- 活跃度: {sentiment.get('activity', 'N/A')}%",
            "",
            "### 最强板块 TOP5:",
        ]
        for s in top_sectors:
            leader_info = f"(领涨: {s.get('leader_name', 'N/A')})" if s.get('leader_name') else ""
            context_lines.append(f"- {s['name']}: {s['change_pct']:+.2f}% {leader_info}")
        
        context_lines.append("")
        context_lines.append("### 最弱板块 TOP3:")
        for s in bottom_sectors:
            context_lines.append(f"- {s['name']}: {s['change_pct']:+.2f}%")

        context_lines.append("")
        context_lines.append("### 人气龙头 TOP5:")
        for l in top_leaders:
            context_lines.append(f"- {l['name']}({l['code']}): ¥{l['price']} ({l['change_pct']:+.1f}%)")
            
        return "\n".join(context_lines)

    @staticmethod
    def generate_review() -> Dict[str, Any]:
        """
        Synchronous version for non-streaming consumers.
        """
        try:
            sentiment = MarketDataService.get_market_sentiment()
            heatmap = MarketDataService.get_sector_heatmap()
            leaders = MarketDataService.get_leader_stocks()
            
            context = DailyReviewService._build_context(sentiment, heatmap, leaders)

            from app.services.llm_provider import LLMProviderManager
            manager = LLMProviderManager()
            client, model_name = manager.get_client()

            if client and model_name:
                prompt = f"请作为 NEXUS AI 首席分析师，基于以下数据生成今日复盘报告：\n\n{context}\n\n报告需包含：机构视角、量化视角、游资视角和 CIO 总结。"
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一个资深投资助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                )
                report = resp.choices[0].message.content.strip()
                return {
                    "report": report,
                    "generated_at": int(time.time()),
                    "data_source": "ai",
                }
            else:
                report = DailyReviewService._generate_template_report(
                    sentiment, heatmap[:5], sorted(heatmap, key=lambda x: x.get("change_pct", 0))[:3], leaders[:5]
                )
                return {
                    "report": report,
                    "generated_at": int(time.time()),
                    "data_source": "template",
                }

        except Exception as e:
            return {
                "report": f"# ⚠️ 复盘生成失败\n\n错误: {str(e)}",
                "generated_at": int(time.time()),
                "data_source": "error",
            }

    @staticmethod
    def _generate_template_report(sentiment, top_sectors, bottom_sectors, top_leaders) -> str:
        """Fallback template logic."""
        up, down = sentiment.get("up_count", 0), sentiment.get("down_count", 0)
        mood = "多头主导" if up > down else "空头主导" if down > up else "震荡平衡"
        
        return f"# 📋 NEXUS 每日复盘 (Template)\n\n市场氛围：{mood}。上涨 {up}，下跌 {down}。"
