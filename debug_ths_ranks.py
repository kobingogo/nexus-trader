import akshare as ak
import traceback

print("Testing THS CXZ (Innovation High Turnover?)...")
try:
    # cxfl = Chuang Xin Feng Liang? (High Volume)
    # let's try cxfl
    df = ak.stock_rank_cxfl_ths()
    print("Columns:", df.columns)
    print(df.head(1).to_string())
except Exception as e:
    print(f"Failed: {e}")

print("\nTesting Heatmap to Leader Aggregation Strategy...")
try:
    # If we use the heatmap summary, can we get enough info?
    df = ak.stock_board_industry_summary_ths()
    print("Heatmap Columns:", df.columns)
    # We need Code. Leader Name is '领涨股'. 
    # Can we get code from name?
    # ak.stock_info_a_code_name() returns a massive df.
    # Is there a search function?
    pass
except Exception as e:
    print(f"Failed: {e}")
