import akshare as ak
import pandas as pd

try:
    print("Fetching market activity via ak.stock_market_activity_legu()...")
    df = ak.stock_market_activity_legu()
    print("Columns:", df.columns.tolist())
    print("Data:")
    print(df)
    
    # Simulate processing logic
    data = dict(zip(df['item'], df['value']))
    print("\nProcessed Dictionary:")
    print(data)
    
except Exception as e:
    print(f"Error: {e}")
