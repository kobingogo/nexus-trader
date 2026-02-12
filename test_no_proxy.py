
import os
# Clear proxy envs
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

import akshare as ak
try:
    print("Fetching '算力概念' constituents (No Proxy)...")
    df = ak.stock_board_concept_cons_em(symbol="算力概念")
    print("Success!")
    print(df.head())
except Exception as e:
    print(f"Error: {e}")
