
import logging
import akshare as ak
import pandas as pd
import requests
from io import StringIO
from typing import List, Dict, Any, Optional
from enum import Enum
import time

logger = logging.getLogger(__name__)

class DataProvider:
    """
    Centralized data provider with failover strategies.
    Order: EM -> THS (Scraping)
    """
    
    _ths_concept_map = {} # Name -> Code

    @staticmethod
    def get_all_concepts() -> List[str]:
        """
        Fetch all concept names.
        Prioritizes EastMoney, falls back to Tonghuashun.
        """
        # 1. Try EastMoney
        try:
            # logger.info("Fetching concepts from EastMoney...")
            df = ak.stock_board_concept_name_em()
            return df['板块名称'].tolist()
        except Exception as e:
            logger.warning(f"EastMoney concept fetch failed: {e}")

        # 2. Try Tonghuashun (and cache mapping)
        try:
            # logger.info("Fetching concepts from Tonghuashun...")
            df = ak.stock_board_concept_name_ths()
            # Cache the mapping for later use in get_concept_stocks
            # df columns: ['name', 'url'] or ['name', 'code'] ?
            # Based on debug output: ['name', 'code']
            if 'code' in df.columns:
                DataProvider._ths_concept_map = dict(zip(df['name'], df['code']))
            elif 'url' in df.columns:
                # Extract code from url if needed, but 'code' column is preferred
                pass
            
            return df['name'].tolist()
        except Exception as e:
            logger.error(f"Tonghuashun concept fetch failed: {e}")
            return []

    @staticmethod
    def _scrape_ths_concept(concept_code: str) -> pd.DataFrame:
        url = f"http://q.10jqka.com.cn/gn/detail/code/{concept_code}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            r = requests.get(url, headers=headers, timeout=10)
            target_encoding = 'gbk'
            r.encoding = target_encoding
            dfs = pd.read_html(StringIO(r.text))
            if dfs:
                return dfs[0]
        except Exception as e:
            logger.error(f"Scraping THS {concept_code} failed: {e}")
        return pd.DataFrame()

    @staticmethod
    def get_concept_stocks(concept_name: str) -> List[Dict[str, Any]]:
        """
        Fetch stocks for a concept.
        Prioritizes EastMoney, falls back to Tonghuashun Scraper.
        """
        # 1. Try EastMoney
        try:
            # logger.info(f"Fetching '{concept_name}' stocks from EastMoney...")
            df = ak.stock_board_concept_cons_em(symbol=concept_name)
            result = []
            for _, row in df.iterrows():
                try:
                    res_item = {
                        "code": row['代码'],
                        "name": row['名称'],
                        "price": float(row['最新价']),
                        "change_pct": float(row['涨跌幅']),
                        "turnover": float(row['成交额']) if '成交额' in row else 0,
                    }
                    result.append(res_item)
                except ValueError:
                    continue
            result.sort(key=lambda x: x['change_pct'], reverse=True)
            return result
        except Exception as e:
            logger.warning(f"EastMoney '{concept_name}' fetch failed: {e}")

        # 2. Try Tonghuashun Scraper
        # If mapping is empty, try to populate it (lazy load)
        if not DataProvider._ths_concept_map:
             try:
                df_map = ak.stock_board_concept_name_ths()
                if 'code' in df_map.columns:
                     DataProvider._ths_concept_map = dict(zip(df_map['name'], df_map['code']))
             except:
                 pass

        if concept_name in DataProvider._ths_concept_map:
            code = DataProvider._ths_concept_map[concept_name]
            logger.info(f"Scraping THS data for '{concept_name}' (Code: {code})")
            df = DataProvider._scrape_ths_concept(code)
            if not df.empty:
                result = []
                for _, row in df.iterrows():
                    try:
                        # THS columns: 序号 代码 名称 现价 涨跌幅(%) ... 成交额(亿) ...
                        # Need to parse '成交额' which might have units
                        # Columns: 序号 代码 名称 现价 涨跌幅(%) 涨跌 涨速(%) 换手(%) 量比 振幅(%) 成交额 流通股 流通市值 市盈率
                        turnover_str = str(row.get('成交额', '0'))
                        turnover = 0.0
                        if '亿' in turnover_str:
                            turnover = float(turnover_str.replace('亿', '')) * 1e8
                        elif '万' in turnover_str:
                             turnover = float(turnover_str.replace('万', '')) * 1e4
                        
                        price = row.get('现价', 0)
                        if price == '--': price = 0
                        
                        change_pct = row.get('涨跌幅(%)', 0)
                        if change_pct == '--': change_pct = 0
                        
                        res_item = {
                            "code": str(row['代码']).zfill(6),
                            "name": row['名称'],
                            "price": float(price),
                            "change_pct": float(change_pct),
                            "turnover": turnover,
                        }
                        result.append(res_item)
                    except Exception as parse_err:
                        # logger.warning(f"Parse error: {parse_err}")
                        continue
                result.sort(key=lambda x: x['change_pct'], reverse=True)
                return result
        
        return []
