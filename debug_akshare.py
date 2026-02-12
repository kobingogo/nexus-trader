import akshare as ak
import traceback

print("Testing THS LXSZ (Consecutive Up)...")
try:
    df = ak.stock_rank_lxsz_ths()
    print("Columns:", df.columns)
    print(df.head(1))
except Exception:
    traceback.print_exc()

print("\nTesting EM ZDT (Limit Up)...") 
# Fallback to EM specific limit up pool if general spot fails context
try:
    # Need date usually for ZDT pool
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    # Tushare/AkShare ZDT usually needs passing a date, let's try getting recent date
    # Actually let's try without date if allowed or pick yesterday
    # ak.stock_zt_pool_em(date='...')
    pass
except Exception:
    pass
