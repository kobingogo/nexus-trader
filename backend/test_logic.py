
import sys
import os
import asyncio
from app.services.logic_chain import LogicChainService

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test():
    print("Testing LogicChainService...")
    
    # 1. Test get_all_concepts
    print("\n--- Fetching All Concepts ---")
    concepts = LogicChainService.get_all_concepts()
    print(f"Total concepts found: {len(concepts)}")
    if concepts:
        print(f"Example concepts: {concepts[:5]}")
    
    # 2. Test search
    print("\n--- Searching Concept '低空' (Low Altitude) ---")
    search_res = LogicChainService.search_concepts("低空")
    print(f"Results: {search_res}")
    
    if search_res:
        target_concept = search_res[0]
        # 3. Test analyze / get leaders
        print(f"\n--- Getting Leaders for '{target_concept}' ---")
        leaders = LogicChainService.get_concept_stocks(target_concept)
        print(f"Found {len(leaders)} stocks.")
        print("Top 5 Leaders:")
        for stock in leaders[:5]:
            print(f"{stock['code']} {stock['name']} +{stock['change_pct']}%")

if __name__ == "__main__":
    asyncio.run(test())
