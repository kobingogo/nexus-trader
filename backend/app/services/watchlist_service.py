import json
import os
from typing import List, Dict, Any
from threading import Lock

# Simple JSON file-based watchlist storage (MVP, no database needed)
WATCHLIST_FILE = os.path.join(os.path.dirname(__file__), "../watchlist.json")
_lock = Lock()


class WatchlistService:
    @staticmethod
    def _load() -> List[Dict[str, str]]:
        """Load watchlist from JSON file."""
        try:
            if os.path.exists(WATCHLIST_FILE):
                with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading watchlist: {e}")
        return []

    @staticmethod
    def _save(watchlist: List[Dict[str, str]]):
        """Save watchlist to JSON file."""
        with _lock:
            try:
                with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
                    json.dump(watchlist, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error saving watchlist: {e}")

    @staticmethod
    def get_watchlist() -> List[Dict[str, str]]:
        """Get the full watchlist."""
        return WatchlistService._load()

    @staticmethod
    def get_codes() -> set:
        """Get a set of all watched stock codes for fast lookup."""
        return {item["code"] for item in WatchlistService._load()}

    @staticmethod
    def add_stock(code: str, name: str, tags: list = None) -> Dict[str, Any]:
        """Add a stock to watchlist. Returns result."""
        watchlist = WatchlistService._load()
        # Check duplicate
        for item in watchlist:
            if item["code"] == code:
                return {"success": False, "message": f"{name}({code}) 已在关注列表中"}
        
        watchlist.append({"code": code, "name": name, "tags": tags or []})
        WatchlistService._save(watchlist)
        return {"success": True, "message": f"已关注 {name}({code})"}

    @staticmethod
    def remove_stock(code: str) -> Dict[str, Any]:
        """Remove a stock from watchlist."""
        watchlist = WatchlistService._load()
        new_list = [item for item in watchlist if item["code"] != code]
        if len(new_list) == len(watchlist):
            return {"success": False, "message": f"股票 {code} 不在关注列表中"}
        
        WatchlistService._save(new_list)
        return {"success": True, "message": f"已取消关注 {code}"}

    @staticmethod
    def update_tags(code: str, tags: list) -> Dict[str, Any]:
        """Update tags for a stock."""
        watchlist = WatchlistService._load()
        for item in watchlist:
            if item["code"] == code:
                item["tags"] = tags
                WatchlistService._save(watchlist)
                return {"success": True, "message": f"标签已更新"}
        return {"success": False, "message": f"股票 {code} 不在关注列表中"}

    @staticmethod
    def is_watched(code: str) -> bool:
        """Check if a stock is watched."""
        return code in WatchlistService.get_codes()

