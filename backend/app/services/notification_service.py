import logging
import aiohttp
import json
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Default Mock URL for development if not set in env
DEFAULT_FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK_URL", "")

class NotificationService:
    """
    Handles sending notifications to external channels (Feishu, etc.)
    """

    @staticmethod
    async def send_feishu_alert(title: str, content: str, level: str = "info"):
        """
        Send a card message to Feishu Webhook.
        """
        webhook_url = DEFAULT_FEISHU_WEBHOOK
        if not webhook_url:
            logger.warning("Feishu Webhook URL not set. Skipping notification.")
            return

        # Map level to color
        color_map = {
            "critical": "red",
            "warning": "yellow",
            "info": "blue"
        }
        color = color_map.get(level, "blue")

        # Construct Feishu Interactive Card
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🧠 NEXUS Brain Alert: {title}"
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "来自 NEXUS Trader 智能体"
                        }
                    ]
                }
            ]
        }

        payload = {
            "msg_type": "interactive",
            "card": card
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to send Feishu alert: {await resp.text()}")
                    else:
                        logger.info(f"Sent Feishu alert: {title}")
        except Exception as e:
            logger.error(f"Error sending Feishu alert: {e}")

    @staticmethod
    async def broadcast(signal: Dict[str, Any]):
        """
        Broadcast a signal to all configured channels based on severity.
        """
        level = signal.get("level", "info")
        type_ = signal.get("type", "unknown")
        message = signal.get("message", "")
        
        # Only notify for Critical or Warning
        if level not in ["critical", "warning"]:
            return

        # Format content
        content = f"**级别**: {level.upper()}\n**类型**: {type_}\n**内容**: {message}\n**时间**: {signal.get('timestamp', '')}"

        # Send to Feishu
        await NotificationService.send_feishu_alert(
            title=f"{type_} Detected", 
            content=content, 
            level=level
        )
