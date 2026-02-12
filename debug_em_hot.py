import akshare as ak
import traceback

def test_func(name, func):
    print(f"\nTesting {name}...")
    try:
        df = func()
        print("Columns:", df.columns)
        print(df.head(1).to_string())
    except Exception as e:
        print(f"Failed: {e}")

# Try EM Hot Rank
test_func("EM Hot Rank (stock_hot_rank_em)", getattr(ak, 'stock_hot_rank_em', lambda: None))

# Try EM Hot Rank Latest (might be same or more details)
test_func("EM Hot Rank Latest (stock_hot_rank_latest_em)", getattr(ak, 'stock_hot_rank_latest_em', lambda: None))

# Try Realtime Detail Rank
test_func("EM Hot Rank Detail Realtime", getattr(ak, 'stock_hot_rank_detail_realtime_em', lambda: None))
