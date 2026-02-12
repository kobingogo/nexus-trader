
import requests
import time
import akshare as ak

def check_sina():
    url = "https://hq.sinajs.cn/list=sz000001"
    headers = {
        "Referer": "https://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    print(f"Checking Sina ({url}) with Referer...")
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"[Sina] Status: {r.status_code}")
        print(f"[Sina] Content: {r.text[:50]}...")
    except Exception as e:
        print(f"[Sina] FAILED: {e}")

def check_ak_ths():
    print("Checking ak.stock_board_industry_summary_ths()...")
    try:
        df = ak.stock_board_industry_summary_ths()
        print(f"[AK THS] Success. Shape: {df.shape}")
        print(df.head())
    except Exception as e:
        print(f"[AK THS] FAILED: {e}")

if __name__ == "__main__":
    check_sina()
    print("-" * 20)
    check_ak_ths()
