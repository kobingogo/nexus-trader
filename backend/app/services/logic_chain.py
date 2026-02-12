
import logging
import time
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_fixed
from app.core.data_provider import DataProvider

logger = logging.getLogger(__name__)

class LogicChainService:
    _concepts_cache = []
    _concepts_cache_time = 0
    CACHE_FILE = "data/concepts_cache.json"

    @staticmethod
    def _load_cache_from_file():
        import json
        import os
        if os.path.exists(LogicChainService.CACHE_FILE):
            try:
                with open(LogicChainService.CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    LogicChainService._concepts_cache = data
                    LogicChainService._concepts_cache_time = time.time()
                    return data
            except Exception as e:
                logger.error(f"Error loading cache file: {e}")
        return []

    @staticmethod
    def _save_cache_to_file(data):
        import json
        import os
        os.makedirs(os.path.dirname(LogicChainService.CACHE_FILE), exist_ok=True)
        try:
            with open(LogicChainService.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache file: {e}")

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_all_concepts() -> List[str]:
        """
        Get all concept names using DataProvider.
        Cache for 1 hour.
        """
        import time
        now = time.time()
        
        # Memory cache
        if LogicChainService._concepts_cache and (now - LogicChainService._concepts_cache_time < 3600):
            return LogicChainService._concepts_cache

        # Dispatch via DataProvider
        # DataProvider handles strategies (EM -> THS -> Mock)
        try:
            concepts = DataProvider.get_all_concepts()
            if concepts:
                LogicChainService._concepts_cache = concepts
                LogicChainService._concepts_cache_time = now
                LogicChainService._save_cache_to_file(concepts)
                return concepts
        except Exception as e:
            logger.error(f"Error in DataProvider.get_all_concepts: {e}")

        # Fallback to file cache
        cached = LogicChainService._load_cache_from_file()
        if cached:
            logger.info("Used file cache for concepts.")
            return cached
        
        return []

    @staticmethod
    def search_concepts(query: str, limit: int = 10) -> List[str]:
        """
        Search for concepts by name.
        """
        all_concepts = LogicChainService.get_all_concepts()
        if not all_concepts:
            return []
        
        # Simple fuzzy match
        results = [c for c in all_concepts if query in c]
        
        # Sort by length (shorter match first) and alphabetically
        results.sort(key=lambda x: (len(x), x))
        
        return results[:limit]

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_concept_stocks(concept_name: str) -> List[Dict[str, Any]]:
        """
        Get constituent stocks for a concept using DataProvider.
        Returns Top stocks by change_pct.
        """
        try:
            return DataProvider.get_concept_stocks(concept_name)
        except Exception as e:
            logger.error(f"Error in DataProvider.get_concept_stocks: {e}")
            return []

    @staticmethod
    def analyze_logic_chain(user_query: str) -> Dict[str, Any]:
        """
        Analyze logic chain for a user query.
        1. Search concept
        2. Find leaders
        """
        concepts = LogicChainService.search_concepts(user_query)
        
        if not concepts:
            return {
                "query": user_query,
                "found_concepts": [],
                "best_match": None,
                "reasoning": f"No concepts found for '{user_query}'",
                "leaders": []
            }
        
        best_match = concepts[0]
        leaders = LogicChainService.get_concept_stocks(best_match)
        
        # Top 5 leaders
        top_leaders = leaders[:5]

        return {
            "query": user_query,
            "found_concepts": concepts,
            "best_match": best_match,
            "reasoning": f"Mapped '{user_query}' to concept '{best_match}'. Top leaders identified by price action.",
            "leaders": top_leaders
        }
