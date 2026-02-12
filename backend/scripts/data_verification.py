#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: NEXUS
@date: 2026-02-12
@desc: Data Verification Script for AkShare (Open Source Financial Data Interface)
"""

import os

# Disable Proxy for Domestic Requests
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['ALL_PROXY'] = ''

import akshare as ak
import pandas as pd
from datetime import datetime

def check_market_index():
    """Check Real-time Market Index (SH000001)"""
    print("\n--- [1] Checking Market Index (SH000001) ---")
    try:
        # Get real-time data for Shanghai Composite Index
        df = ak.stock_zh_index_spot()
        sh_index = df[df['代码'] == 'sh000001']
        
        if not sh_index.empty:
            print(f"Current Index: {sh_index.iloc[0]['名称']} ({sh_index.iloc[0]['代码']})")
            print(f"Latest Price: {sh_index.iloc[0]['最新价']}")
            print(f"Change Pct: {sh_index.iloc[0]['涨跌幅']}%")
            print("✅ SUCCESS: Market Index Data Fetched.")
        else:
            print("❌ FAILURE: SH000001 not found.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def check_individual_stock(symbol="600519"):
    """Check Individual Stock Real-time Data (Moutai)"""
    print(f"\n--- [2] Checking Stock Data ({symbol}) ---")
    try:
        # Get real-time data for individual stock
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == symbol]
        
        if not stock.empty:
            print(f"Name: {stock.iloc[0]['名称']}")
            print(f"Latest Price: {stock.iloc[0]['最新价']}")
            print(f"Turnover Ratio: {stock.iloc[0]['换手率']}%")
            print(f"Volume Ratio: {stock.iloc[0]['量比']}")
            print("✅ SUCCESS: Stock Data Fetched.")
        else:
            print(f"❌ FAILURE: Stock {symbol} not found.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def check_sector_concepts():
    """Check Top 5 Concepts (Hot Sectors)"""
    print("\n--- [3] Checking Hot Concepts (Top 5) ---")
    try:
        # Get real-time concept board data
        df = ak.stock_board_concept_name_em()
        top5 = df.head(5)
        
        print("Top 5 Concepts by Change %:")
        for index, row in top5.iterrows():
            print(f"#{index+1} {row['板块名称']} (+{row['涨跌幅']}%) | Laggard: {row['领涨股票']} (+{row['领涨股票-涨跌幅']}%)")
            
        print("✅ SUCCESS: Concept Data Fetched.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print(f"🚀 NEXUS Data Verification Started at {datetime.now()}")
    
    check_market_index()
    check_individual_stock()
    check_sector_concepts()
    
    print("\n🏁 Verification Complete.")
