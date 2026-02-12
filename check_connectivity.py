
import requests
import time

def check(url, name):
    print(f"Checking {name} ({url})...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    start = time.time()
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"[{name}] Status: {r.status_code}, Time: {time.time()-start:.2f}s")
        if r.status_code != 200:
            print(f"[{name}] Content (excerpt): {r.text[:100]}")
    except Exception as e:
        print(f"[{name}] FAILED: {e}")

if __name__ == "__main__":
    check("https://hq.sinajs.cn/list=sz000001", "Sina Quote")
    check("http://q.10jqka.com.cn/gn/detail/code/300846/", "THS Concept")
    check("http://push2.eastmoney.com/api/qt/clist/get", "EastMoney API")
