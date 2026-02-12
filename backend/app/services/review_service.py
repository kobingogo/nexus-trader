import os
import time
from typing import Dict, Any
from openai import OpenAI
from app.services.market_data import MarketDataService


class DailyReviewService:
    @staticmethod
    def generate_review() -> Dict[str, Any]:
        """
        Generate a daily market review report.
        Aggregates sentiment + heatmap + leaders data, then uses LLM 
        (or template fallback) to produce a Markdown report.
        """
        try:
            # 1. Gather data
            sentiment = MarketDataService.get_market_sentiment()
            heatmap = MarketDataService.get_sector_heatmap()
            leaders = MarketDataService.get_leader_stocks()

            # Top 5 sectors
            top_sectors = heatmap[:5] if heatmap else []
            bottom_sectors = sorted(heatmap, key=lambda x: x.get("change_pct", 0))[:3] if heatmap else []
            
            # Top 5 leaders
            top_leaders = leaders[:5] if leaders else []

            # 2. Build context for LLM
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
                context_lines.append(f"- {s['name']}: {s['change_pct']:+.2f}% (领涨: {s.get('leader_name', 'N/A')})")
            
            context_lines.append("")
            context_lines.append("### 最弱板块 TOP3:")
            for s in bottom_sectors:
                context_lines.append(f"- {s['name']}: {s['change_pct']:+.2f}%")

            context_lines.append("")
            context_lines.append("### 人气龙头 TOP5:")
            for l in top_leaders:
                context_lines.append(f"- {l['name']}({l['code']}): ¥{l['price']} ({l['change_pct']:+.1f}%)")

            context = "\n".join(context_lines)

            # 3. Try LLM generation
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

            if api_key:
                prompt = f"""
角色：资深A股复盘分析师 (NEXUS AI)
任务：根据以下今日市场数据，生成一份简洁精炼的每日复盘报告 (Markdown格式)。

{context}

请生成报告，包含以下章节：
1. 📊 今日总结 (一句话概括今日行情特征)
2. 🔥 最强方向 (哪些板块最强，为什么)
3. ⚠️ 亏钱效应 (哪里是亏钱重灾区)
4. 🎯 明日策略 (NEXUS 建议：进攻/防守/观望 + 理由)
5. 💡 关键个股提示 (值得关注的龙头)

要求：语言简洁有力，像一个老师傅在复盘，不要废话。
"""
                client = OpenAI(api_key=api_key, base_url=base_url)
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": "你是 NEXUS AI，一个专业的A股复盘分析师。输出 Markdown 格式。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                )
                report = response.choices[0].message.content
            else:
                # Fallback: template-based report
                report = DailyReviewService._generate_template_report(
                    sentiment, top_sectors, bottom_sectors, top_leaders
                )

            return {
                "report": report,
                "generated_at": int(time.time()),
                "data_source": "llm" if api_key else "template",
            }
        except Exception as e:
            print(f"Error generating daily review: {e}")
            return {
                "report": f"# ⚠️ 复盘生成失败\n\n错误: {str(e)}",
                "generated_at": int(time.time()),
                "data_source": "error",
            }

    @staticmethod
    def _generate_template_report(
        sentiment: Dict,
        top_sectors: list,
        bottom_sectors: list,
        top_leaders: list,
    ) -> str:
        """Fallback template when no LLM API key is configured."""
        up = sentiment.get("up_count", 0)
        down = sentiment.get("down_count", 0)
        lu = sentiment.get("limit_up_count", 0)
        ld = sentiment.get("limit_down_count", 0)
        activity = sentiment.get("activity", 0)

        # Determine mood
        if up > down * 1.5:
            mood = "多头主导，赚钱效应扩散"
            strategy = "进攻"
            strategy_detail = "情绪偏强，可积极参与强势板块龙头。注意追高风险。"
        elif down > up * 1.5:
            mood = "空头主导，亏钱效应蔓延"
            strategy = "防守"
            strategy_detail = "情绪偏弱，控制仓位，等待企稳信号。"
        else:
            mood = "多空胶着，结构性行情"
            strategy = "观望"
            strategy_detail = "分化明显，精选个股，避免追涨杀跌。"

        top_str = "\n".join(
            [f"- **{s['name']}**: {s['change_pct']:+.2f}% (领涨: {s.get('leader_name', '-')})" for s in top_sectors]
        ) or "- 无数据"

        bottom_str = "\n".join(
            [f"- **{s['name']}**: {s['change_pct']:+.2f}%" for s in bottom_sectors]
        ) or "- 无数据"

        leader_str = "\n".join(
            [f"- **{l['name']}** ({l['code']}): ¥{l['price']} ({l['change_pct']:+.1f}%)" for l in top_leaders]
        ) or "- 无数据"

        return f"""# 📋 NEXUS 每日复盘

> ⚠️ 本报告由模板生成（未配置 LLM API Key）。配置 `OPENAI_API_KEY` 可获得 AI 深度分析。

## 📊 今日总结

**{mood}**。上涨 {up} 家，下跌 {down} 家，涨停 {lu} 家，跌停 {ld} 家，活跃度 {activity}%。

## 🔥 最强方向

{top_str}

## ⚠️ 亏钱效应

{bottom_str}

## 🎯 明日策略：**{strategy}**

{strategy_detail}

## 💡 人气龙头

{leader_str}

---
*NEXUS AI · 理性副驾驶*
"""
