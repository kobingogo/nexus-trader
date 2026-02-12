import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import akshare as ak
import os
import random
import datetime

# --- 配置 ---
st.set_page_config(page_title="NEXUS Trader AI", layout="wide", page_icon="📈")

# --- UI 样式 ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
    .stTextInput > div > div > input {
        text-align: center;
        font-size: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏 ---
with st.sidebar:
    st.title("🤖 NEXUS Trader")
    st.markdown("---")
    
    st.header("⚙️ 系统设置")
    
    # 1. 数据源选择
    data_mode = st.radio("数据模式 (Data Mode)", ["Mock (模拟演示)", "Real (AKShare实盘)"], index=0, help="如果网络不通，请先使用模拟模式体验功能。")
    
    # 2. 网络代理设置 (关键!)
    use_proxy = st.checkbox("启用代理 (Proxy)", value=False, help="如果 AKShare 报错 ProxyError，尝试开启此项并填入本地代理地址。")
    proxy_url = st.text_input("代理地址 (HTTP/HTTPS)", "http://127.0.0.1:7890", disabled=not use_proxy)

    if use_proxy:
        os.environ['http_proxy'] = proxy_url
        os.environ['https_proxy'] = proxy_url
        os.environ['all_proxy'] = proxy_url
    else:
        # 清理代理，防止残留
        for k in ['http_proxy', 'https_proxy', 'all_proxy']:
            if k in os.environ:
                del os.environ[k]

    st.markdown("---")
    st.header("🧠 AI 配置")
    ai_model = st.selectbox("分析模型", ["NEXUS-Lite (本地规则)", "OpenAI/DeepSeek (API)"])
    if ai_model == "OpenAI/DeepSeek (API)":
        api_key = st.text_input("API Key", type="password")
    
    st.markdown("---")
    with st.expander("🛠️ 网络诊断 (Network Diagnosis)"):
        test_url = st.text_input("测试目标 URL", "https://www.baidu.com")
        if st.button("开始测试连接"):
            try:
                st.write(f"正在连接: `{test_url}` ...")
                import requests
                # 显式使用当前的环境变量配置
                proxies = {}
                if use_proxy:
                    proxies = {"http": proxy_url, "https": proxy_url}
                
                resp = requests.get(test_url, proxies=proxies, timeout=5)
                st.success(f"连接成功! 状态码: {resp.status_code}")
                st.json(dict(resp.headers))
            except Exception as e:
                st.error(f"连接失败: {e}")
                st.markdown(f"**当前代理配置:** `{proxy_url if use_proxy else 'Disabled'}`")
                st.markdown("**建议:**\n1. 检查 Clash 是否开启 'Allow LAN' (允许局域网连接)\n2. 尝试将代理地址改为 `http://127.0.0.1:7890`\n3. 检查端口号是否正确")

# --- 核心函数 ---

def get_mock_data(ticker, days=100):
    """生成逼真的模拟K线数据"""
    dates = pd.date_range(end=datetime.date.today(), periods=days)
    base_price = random.uniform(10, 200)
    data = []
    price = base_price
    for d in dates:
        change = random.uniform(-0.05, 0.05)
        open_p = price * (1 + random.uniform(-0.01, 0.01))
        close_p = price * (1 + change)
        high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.02))
        low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.02))
        vol = random.randint(1000, 100000)
        data.append([d, open_p, close_p, high_p, low_p, vol])
        price = close_p
    
    df = pd.DataFrame(data, columns=['date', 'open', 'close', 'high', 'low', 'volume'])
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    # 模拟基本信息
    return df, {"name": f"模拟股票-{ticker}", "price": price, "change": (price - base_price)/base_price * 100}

def get_real_data(ticker, use_proxy=False):
    """尝试从 AKShare 获取真实数据"""
    # 备份相关的环境变量
    env_keys = ['http_proxy', 'https_proxy', 'all_proxy', 'no_proxy']
    env_backup = {k: os.environ.get(k) for k in env_keys}

    if not use_proxy:
        # 强制直连：清除代理变量并设置 no_proxy=* 以忽略系统代理
        for k in ['http_proxy', 'https_proxy', 'all_proxy']:
            if k in os.environ:
                del os.environ[k]
        os.environ['no_proxy'] = '*'
    
    # 开始尝试获取数据
    # 开始尝试获取数据
    try:
        last_exception = None
        for attempt in range(3):
            try:
                # 1. 获取日线历史数据 (比获取全市场实时数据更稳定)
                hist_df = ak.stock_zh_a_hist(symbol=ticker, period="daily", start_date="20230101", adjust="qfq")
                # 重命名列，包含涨跌幅
                hist_df.rename(columns={
                    '日期': 'date', '开盘': 'open', '收盘': 'close', 
                    '最高': 'high', '最低': 'low', '成交量': 'volume',
                    '涨跌幅': 'pct_chg'
                }, inplace=True)
                
                if hist_df.empty:
                    return None, None

                # 2. 获取个股基础信息 (仅获取名称)
                try:
                    info_df = ak.stock_individual_info_em(symbol=ticker)
                    # 尝试获取股票名称，支持多种可能的字段名
                    name_row = info_df[info_df['item'].isin(['股票名称', '股票简介', '名称'])]
                    if not name_row.empty:
                        name = name_row['value'].values[0]
                    else:
                        name = f"股票代码-{ticker}"
                except Exception:
                    name = f"股票代码-{ticker}"
                
                # 使用最近一天的当做"当前"价格 (注意: 盘中可能不是实时的 tick 级数据)
                latest = hist_df.iloc[-1]
                price = latest['close']
                change = latest['pct_chg']
                
                return hist_df, {"name": name, "price": price, "change": change}
            except Exception as e:
                last_exception = e
                # 等待一小段时间后重试
                import time
                time.sleep(1)
                continue
                
        # 如果重试 3 次后仍然失败，抛出最后的异常
        mode_str = "Proxy" if use_proxy else "Direct"
        st.error(f"数据获取失败 ({mode_str} Mode - {last_exception}). 建议检查代理设置或网络连通性。")
        return None, None
    finally:
        # 恢复环境变量
        for k, v in env_backup.items():
            if v is not None:
                os.environ[k] = v
            else:
                # 如果原来不存在，现在存在了，则删除 (恢复到不存在的状态)
                if k in os.environ:
                    del os.environ[k]

def plot_chart(df, ticker_name):
    """绘制交互式K线图"""
    fig = go.Figure(data=[go.Candlestick(x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])
    fig.update_layout(
        title=f'{ticker_name} K线走势',
        xaxis_title='日期',
        yaxis_title='价格',
        height=500,
        template="plotly_dark"
    )
    return fig

def ai_analyze(df, info):
    """模拟 AI 分析逻辑"""
    # 简单的技术指标计算
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    current_price = df['close'].iloc[-1]
    
    trend = "上涨" if ma5 > ma20 else "下跌"
    signal = "买入" if current_price > ma5 and ma5 > ma20 else "观望/卖出"
    
    return f"""
    ### 🤖 NEXUS AI 分析报告
    
    **目标标的**: {info['name']}
    
    **技术面扫描**:
    - **当前趋势**: 短期均线(MA5) {'>' if ma5 > ma20 else '<'} 长期均线(MA20)，整体呈现 **{trend}** 态势。
    - **信号判定**: 基于简单策略，建议 **{signal}**。
    
    **风险提示**:
    - 当前价格 {current_price:.2f}，距离 MA20 乖离率 {(current_price-ma20)/ma20*100:.2f}%。
    - *注: 市场有风险，AI 仅供参考。*
    """

# --- 主界面 ---

col1, col2 = st.columns([3, 1])

with col1:
    st.title("📊 股票行情 AI 分析台")

with col2:
    ticker = st.text_input("输入股票代码 (如 600519)", "600519")
    if st.button("🚀 开始分析", use_container_width=True):
        with st.spinner('正在连接 NEXUS 数据中心...'):
            if data_mode.startswith("Mock"):
                df, info = get_mock_data(ticker)
            else:
                df, info = get_real_data(ticker, use_proxy)
            
            if df is not None:
                # 1. 顶部指标
                m1, m2, m3 = st.columns(3)
                m1.metric("股票名称", info['name'])
                m2.metric("当前价格", f"¥{info['price']:.2f}")
                m3.metric("涨跌幅", f"{info['change']:.2f}%", delta_color="normal")
                
                # 2. 图表
                st.plotly_chart(plot_chart(df, info['name']), use_container_width=True)
                
                # 3. AI 分析
                st.markdown("---")
                st.info("💡 AI 正在思考中...")
                analysis = ai_analyze(df, info)
                st.markdown(analysis)
                
            else:
                st.error("未找到数据，请检查代码或网络设置。")
