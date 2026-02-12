import os
import time
from typing import Dict, Any
from openai import OpenAI
from datetime import datetime
from app.services.market_data import MarketDataService


class DailyReviewService:
    @staticmethod
    def stream_review():
        """
        Stream the daily review generation (yields chunks).
        Format: Server-Sent Events (SSE) style or just raw text chunks.
        We will use raw text chunks for simplicity in this MVP, 
        or a simple JSON structure line by line.
        
        Yields:
            str: JSON string with "type" and "content"
        """
        import json
        
        # 1. Gather data (Synchronous part)
        yield json.dumps({"type": "status", "content": "正在获取市场数据..."}) + "\n"
        
        try:
            sentiment = MarketDataService.get_market_sentiment()
            heatmap = MarketDataService.get_sector_heatmap()
            leaders = MarketDataService.get_leader_stocks()
            
            # Context building... (Reuse logic or refactor to shared method)
            # For brevity, I'll duplicate the context building here or we extracts it.
            # Let's extract context building to a helper to avoid code duplication.
            context = DailyReviewService._build_context(sentiment, heatmap, leaders)
            
            yield json.dumps({"type": "status", "content": "数据获取完成，正在生成分析..."}) + "\n"
            
            # 2. Get LLM Client
            from app.services.llm_provider import LLMProviderManager
            manager = LLMProviderManager()
            client, model_name = manager.get_client()
            
            if not client:
                 yield json.dumps({"type": "error", "content": "未配置 LLM，无法流式生成。"}) + "\n"
                 return

            # 3. Stream Perspectives
            perspectives = [
                {"key": "institutional", "title": "🏛️ 机构视角", "prompt": DailyReviewService.PROMPTS['institutional']},
                {"key": "quant", "title": "📊 量化视角", "prompt": DailyReviewService.PROMPTS['quant']},
                {"key": "hot_money", "title": "⚡ 游资视角", "prompt": DailyReviewService.PROMPTS['hot_money']},
            ]
            
            full_report_parts = [f"# 📈 NEXUS 深度复盘 ({time.strftime('%Y-%m-%d')})\n\n"]
            perspective_outputs = []
            
            yield json.dumps({"type": "chunk", "content": full_report_parts[0]}) + "\n"

            for p in perspectives:
                yield json.dumps({"type": "status", "content": f"正在生成 {p['title']}..."}) + "\n"
                
                header = f"## {p['title']}\n\n"
                yield json.dumps({"type": "chunk", "content": header}) + "\n"
                full_report_parts.append(header)
                
                user_prompt = f"{p['prompt']}\n\n【市场数据】\n{context}\n\n请输出你的分析段落（Markdown格式，不含标题，300字以内）。"
                
                current_section_content = ""
                
                try:
                    stream = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "你是 NEXUS AI 交易系统的分身。"},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        stream=True
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            c = chunk.choices[0].delta.content
                            yield json.dumps({"type": "chunk", "content": c}) + "\n"
                            current_section_content += c
                    
                    yield json.dumps({"type": "chunk", "content": "\n\n"}) + "\n"
                    full_report_parts.append(current_section_content + "\n\n")
                    perspective_outputs.append(f"### {p['title']}\n\n{current_section_content}")
                    
                except Exception as e:
                    error_msg = f"(生成失败: {str(e)})\n\n"
                    yield json.dumps({"type": "chunk", "content": error_msg}) + "\n"
                    full_report_parts.append(error_msg)
                    perspective_outputs.append(f"### {p['title']}\n\n(生成失败)")

            # 4. Stream Summary
            yield json.dumps({"type": "status", "content": "正在生成最终汇总..."}) + "\n"
            
            combined_views = "\n\n".join(perspective_outputs)
            summary_prompt = f"{DailyReviewService.PROMPTS['summary']}\n\n【三方观点】\n{combined_views}\n\n请输出总结。"
            
            # For summary, we want to inject it at the top, but used streaming logic which appends.
            # In streaming UI, typically we just append. 
            # If we want the specific "Insert summary at top" logic, we might need to change UI to having specific slots.
            # OR we just append the summary at the END for the streaming version, which is also a valid flow (Conclusion at the end).
            # Let's put Summary at the END for streaming flow for better UX (reading flow).
            
            yield json.dumps({"type": "chunk", "content": "## 🏁 首席回顾 (CIO Summary)\n\n"}) + "\n"
            
            try:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是 NEXUS AI 首席投资官。"},
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.6,
                    stream=True
                )
                 
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        c = chunk.choices[0].delta.content
                        yield json.dumps({"type": "chunk", "content": c}) + "\n"
                
                yield json.dumps({"type": "chunk", "content": "\n\n---\n*NEXUS AI · 深度复盘系统*" }) + "\n"
                
            except Exception as e:
                yield json.dumps({"type": "chunk", "content": f"(汇总生成失败: {e})"}) + "\n"

            yield json.dumps({"type": "done", "content": ""}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    PROMPTS = {
        "institutional": """
角色：顶级公募基金经理
任务：分析市场基本面和宏观逻辑。
关注点：
1. 市场成交量与流动性变化。
2. 主流板块（如科技、新能源、消费、金融）的趋势性机会。
3. 风格切换（大盘vs小盘，价值vs成长）。
输出风格：专业、理性、宏观视野。
""",
        "quant": """
角色：资深量化交易员
任务：分析市场数据特征。
关注点：
1. 涨跌家数比、涨停炸板率、赚钱效应数据。
2. 市场广度与情绪指标（过热/冰点）。
3. 资金流向异常点。
输出风格：客观、数据驱动、注重概率。
""",
        "hot_money": """
角色：顶级游资大佬
任务：分析短线情绪和题材博弈。
关注点：
1. 连板高度、断板反馈、核按钮情况。
2. 题材持续性与龙头的带动作用。
3. 情绪周期（启动、发酵、高潮、退潮）。
输出风格：犀利、直接、且富有激情（使用“核按钮”、“大面”、“弱转强”等术语）。
""",
        "summary": """
角色：NEXUS 首席投资官 (CIO)
任务：汇总三方观点，给出最终市场定调和策略。
请输出：
1. 🎯 **市场定调**：一句话定义当前阶段。
2. 🛡️ **核心策略**：具体的仓位建议和操作方向。
3. ⭐ **明日重点**：最值得关注的一个方向或风险点。
风格：权威、果断、高屋建瓴。
"""
    }

    @staticmethod
    def _build_context(sentiment, heatmap, leaders) -> str:
        # Top sectors
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
        Generate a daily market review report with multi-perspective analysis.
        Perspectives: Institutional, Quantitative, Hot Money.
        Final Summary: Senior Investor.
        """
        try:
            # 1. Gather data
            sentiment = MarketDataService.get_market_sentiment()
            heatmap = MarketDataService.get_sector_heatmap()
            leaders = MarketDataService.get_leader_stocks()

            # Top sectors
            top_sectors = heatmap[:5] if heatmap else []
            bottom_sectors = sorted(heatmap, key=lambda x: x.get("change_pct", 0))[:3] if heatmap else []
            
            # Leaders
            top_leaders = leaders[:5] if leaders else []

            # 2. Build context for LLM
            context = DailyReviewService._build_context(sentiment, top_sectors, top_leaders)
            # Note: _build_context expects (sentiment, heatmap, leaders) or slightly adapted.
            # My helper _build_context above takes (sentiment, heatmap, leaders) and processes top/bottom inside.
            # But here we already processed them. To keep it clean, let's just make _build_context strictly take the raw data 
            # or we adjust the call. 
            # Let's adjust the helpers to take processing lists if we want to reuse exactly, 
            # OR just calling the helper with raw data is cleaner if we have raw data.
            # Actually I can just refactor generate_review to Use the SAME helper I just added.
            context = DailyReviewService._build_context(sentiment, heatmap, leaders)

            # 3. Get LLM Client
            from app.services.llm_provider import LLMProviderManager
            manager = LLMProviderManager()
            client, model_name = manager.get_client()

            if client and model_name:
                # Define personas and prompts
                perspectives = [
                    {
                        "role": "Institutional",
                        "title": "🏛️ 机构视角 (Institutional)",
                        "prompt": """
角色：顶级公募基金经理
任务：分析市场基本面和宏观逻辑。
关注点：
1. 市场成交量与流动性变化。
2. 主流板块（如科技、新能源、消费、金融）的趋势性机会。
3. 风格切换（大盘vs小盘，价值vs成长）。
输出风格：专业、理性、宏观视野。
                        """
                    },
                    {
                        "role": "Quantitative",
                        "title": "📊 量化视角 (Quantitative)",
                        "prompt": """
角色：资深量化交易员
任务：分析市场数据特征。
关注点：
1. 涨跌家数比、涨停炸板率、赚钱效应数据。
2. 市场广度与情绪指标（过热/冰点）。
3. 资金流向异常点。
输出风格：客观、数据驱动、注重概率。
                        """
                    },
                    {
                        "role": "HotMoney",
                        "title": "⚡ 游资视角 (Hot Money)",
                        "prompt": """
角色：顶级游资大佬
任务：分析短线情绪和题材博弈。
关注点：
1. 连板高度、断板反馈、核按钮情况。
2. 题材持续性与龙头的带动作用。
3. 情绪周期（启动、发酵、高潮、退潮）。
输出风格：犀利、直接、且富有激情（使用“核按钮”、“大面”、“弱转强”等术语）。
                        """
                    }
                ]

                full_report_parts = [f"# 📈 NEXUS 深度复盘 ({datetime.now().strftime('%Y-%m-%d')})\n"]
                
                # We will collect the partial outputs to feed into the summary
                perspective_outputs = []

                # Generate perspectives sequentially
                for p in perspectives:
                    user_prompt = f"""
{p['prompt']}

【市场数据】
{context}

请输出你的分析段落（Markdown格式，不含标题，300字以内）。
"""
                    try:
                        resp = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "你是 NEXUS AI 交易系统的分身。"},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.7,
                        )
                        content = resp.choices[0].message.content.strip()
                        perspective_outputs.append(f"### {p['title']}\n\n{content}")
                        full_report_parts.append(f"## {p['title']}\n\n{content}\n")
                    except Exception as e:
                        print(f"Error generating {p['role']} view: {e}")
                        perspective_outputs.append(f"### {p['title']}\n\n(分析生成失败)")

                # Generate Final Summary
                combined_views = "\n\n".join(perspective_outputs)
                summary_prompt = f"""
角色：NEXUS 首席投资官 (CIO)
任务：汇总以上三方观点，给出最终市场定调和策略。

【三方观点】
{combined_views}

请输出：
1. 🎯 **市场定调**：一句话定义当前阶段（如：牛市初期/震荡磨底/情绪退潮）。
2. 🛡️ **核心策略**：具体的仓位建议（满仓/半仓/空仓）和操作方向。
3. ⭐ **明日重点**：最值得关注的一个方向或风险点。

风格：权威、果断、高屋建瓴。
"""
                try:
                    summary_resp = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "你是 NEXUS AI 首席投资官。"},
                            {"role": "user", "content": summary_prompt}
                        ],
                        temperature=0.6,
                    )
                    summary_content = summary_resp.choices[0].message.content.strip()
                    # Insert summary at the beginning (after title)
                    full_report_parts.insert(1, f"\n{summary_content}\n\n---\n")
                except Exception as e:
                    print(f"Error generating summary: {e}")

                final_report = "\n".join(full_report_parts)
                
                # Append disclaimer
                final_report += "\n\n---\n*NEXUS AI · 深度复盘系统*"

                return {
                    "report": final_report,
                    "generated_at": int(time.time()),
                    "data_source": "ai_ensemble",
                }

            else:
                # Fallback: template-based report
                report = DailyReviewService._generate_template_report(
                    sentiment, top_sectors, bottom_sectors, top_leaders
                )
                return {
                    "report": report,
                    "generated_at": int(time.time()),
                    "data_source": "template",
                }

        except Exception as e:
            print(f"Error generating daily review: {e}")
            import traceback
            traceback.print_exc()
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
