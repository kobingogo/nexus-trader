
import sys
import os
import asyncio
from app.services.logic_chain import LogicChainService

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test():
    print("Testing LogicChainService for '算力'...")
    
    # Be sure to clear cache if needed, but here it's fresh process
    print("\n--- Searching '算力' ---")
    search_res = LogicChainService.search_concepts("算力")
    print(f"Results: {search_res}")
    
    if search_res:
        target_concept = search_res[0]
        print(f"\n--- Getting Leaders for '{target_concept}' ---")
        try:
            leaders = LogicChainService.get_concept_stocks(target_concept)
            print(f"Found {len(leaders)} stocks.")
            print("Top 5 Leaders:")
            for stock in leaders[:5]:
                print(f"{stock['code']} {stock['name']} +{stock['change_pct']}%")
        except Exception as e:
            print(f"Error getting leaders: {e}")
            sys.exit(1)
    else:
        print("No concept found for '算力'")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
