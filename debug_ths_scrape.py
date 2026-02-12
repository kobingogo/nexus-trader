
import requests
import pandas as pd
from io import StringIO

def test_scrape(code):
    url = f"http://q.10jqka.com.cn/gn/detail/code/{code}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"Fetching {url}...")
    try:
        r = requests.get(url, headers=headers)
        r.encoding = 'gbk' # THS widely uses gbk
        print(f"Status: {r.status_code}")
        
        # Look for table
        dfs = pd.read_html(StringIO(r.text))
        if dfs:
            print("Table found!")
            df = dfs[0]
            print(df.head())
            return df
        else:
            print("No table found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scrape("308828") # 东数西算
