
import akshare as ak
import time

try:
    print("Fetching THS concepts...")
    df_all = ak.stock_board_concept_name_ths()
    print(f"Columns: {df_all.columns.tolist()}")
    
    # THS concepts usually have "concept_url" or similar, name is usually "name"
    concepts = df_all['name'].tolist()
    matches = [c for c in concepts if "算力" in c]
    print(f"Found matches for '算力' (THS): {matches}")

    for m in matches:
        print(f"\nFetching constituents for '{m}' (THS)...")
        try:
            # symbol for ths might need to be specific or just name
            df = ak.stock_board_concept_cons_ths(symbol=m)
            print(f"Success! {len(df)} stocks found.")
            print(df.head())
            break 
        except Exception as e:
            print(f"Failed for '{m}': {e}")
        time.sleep(1)

except Exception as e:
    print(f"Global Error: {e}")
