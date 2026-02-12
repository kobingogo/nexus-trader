import akshare as ak
import pandas as pd
from datetime import datetime
import time
import traceback

def test_func(name, func, **kwargs):
    print(f"\nTesting {name}...")
    try:
        df = func(**kwargs)
        if isinstance(df, pd.DataFrame):
            print("Columns:", df.columns)
            print(df.to_string()) # Print all rows
            print("Shape:", df.shape)
        else:
            print("Result:", df)
    except Exception as e:
        print(f"Failed: {e}")

test_func("Market Activity Legu (stock_market_activity_legu)", getattr(ak, 'stock_market_activity_legu', lambda: None))
