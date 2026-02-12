# NEXUS Trader (A-Share Edition) - Technical Architecture Document v1.0

**Version:** 1.0 (MVP)  
**Date:** 2026-02-11  
**Author:** NEXUS (Assisted by Bingo)  
**Status:** Draft

---

## 1. System Overview (系统概览)

NEXUS Trader 采用 **前后端分离 (Client-Server)** 架构，以 **实时数据流 (Real-time Data Stream)** 为核心驱动力。

**核心设计理念：**
*   **轻量化 (Lightweight):** MVP 阶段不引入重型消息队列 (Kafka)，使用 Redis Pub/Sub。
*   **模块化 (Modular):** 数据采集、清洗、计算、推送解耦。
*   **高可用 (HA):** 盘中 4 小时不可宕机，即使部分数据源失效，也要有 Fallback 机制。

---

## 2. Technology Stack (技术栈)

### 2.1 Backend (后端)
*   **Language:** Python 3.10+
*   **Framework:** **FastAPI** (高性能异步 Web 框架，适合 I/O 密集型任务)。
*   **Task Queue:** **Celery** + Redis (异步任务调度，如：每日复盘、盘后数据清洗)。
*   **WebSocket:** FastAPI WebSocket (实时推送行情、异动提醒)。

### 2.2 Frontend (前端)
*   **Framework:** **React** (Next.js 可选) or **Vue 3**。
*   **UI Library:** Ant Design / Tailwind CSS (暗黑模式优化)。
*   **Charts:** **Apache ECharts** (国内生态最强，适合 A 股 K 线/分时图) + **TradingView Lightweight Charts** (轻量级)。

### 2.3 Data (数据层)
*   **Real-time Cache:** **Redis** (核心！存储 Ticks、分钟级 K 线、异动信号)。
*   **Historical DB:** **PostgreSQL** (TimescaleDB 插件可选，存储日线、F10 资料)。
    *   *备选：ClickHouse (如果数据量巨大，MVP 暂不需要)*
*   **Data Source (数据源):**
    *   **AkShare:** (GitHub Star 数万的开源财经数据接口，覆盖全) - **主要数据源**。
    *   **Tushare Pro:** (稳定，但部分需积分) - **备用/校验**。
    *   **Crawler:** (针对特定券商 APP 的实时异动接口抓取)。

### 2.4 DevOps
*   **Container:** Docker
*   **Orchestration:** Docker Compose
*   **Monitoring:** Prometheus + Grafana (监控系统健康度)。

### 2.5 AI Layer (AI 智能层)
*   **LLM Core:** OpenAI GPT-4o / Anthropic Claude 3.5 (通过 API 调用) 或 本地部署 DeepSeek-R1 (若显存允许)。
*   **Agent Framework:** **LangChain** / **AutoGen** (用于构建 Agent 流程)。
*   **Function Calling:** 定义 `tools` (如 `get_price`, `get_news`, `check_risk`) 供 LLM 调用。
*   **Memory:** Vector DB (ChromaDB / Faiss) 存储历史新闻、策略文档、用户偏好。

---

## 3. Architecture Diagram (架构图)

```mermaid
graph TD
    User[用户 (Browser/App)] -->|WebSocket (实时行情/异动)| Gateway[NEXUS Gateway (FastAPI)]
    User -->|HTTP (历史数据/复盘)| Gateway
    User -->|Chat (自然语言指令)| AgentService[AI Agent Service]

    subgraph "Data Processing Layer (数据处理层)"
        Gateway -->|Read| Redis[(Redis - 实时热数据)]
        Gateway -->|Read/Write| DB[(PostgreSQL - 历史冷数据)]

        Spider[数据采集器 (Spider/AkShare)] -->|Write (Ticks/KLine)| Redis
        Spider -->|Write (Daily Close)| DB
        
        Analyzer[异动分析引擎 (Analysis Engine)] -->|Subscribe| Redis
        Analyzer -->|Publish (Alerts)| Redis
    end

    subgraph "AI Agent Layer (智能层)"
        AgentService -->|Call Tools| Gateway
        AgentService -->|Query| DB
        AgentService -->|RAG| VectorDB[(Vector DB - 知识库)]
        AgentService -->|LLM API| LLM[Large Language Model]
    end

    subgraph "External World (外部世界)"
        Spider -->|Request| AkShare[AkShare API]
        Spider -->|Request| EastMoney[东方财富/同花顺]
    end
```

---

## 4. Key Modules Design (核心模块设计)

### 4.1 Data Ingestion (数据采集) - `nexus-spider`
*   **职责：** 从 AkShare/API 获取实时行情。
*   **频率：**
    *   L1 行情 (Level-1): 每 3 秒一次 (快照)。
    *   异动数据: 轮询 (Poll) 或 长轮询 (Long Poll)。
*   **策略：** 多源并发，去重清洗。

### 4.2 Real-time Analysis (实时分析) - `nexus-brain`
*   **职责：** 计算“情绪”与“异动”。
*   **算法示例 (MVP):**
    *   **涨速监测:** `(Current_Price - Price_1min_ago) / Price_1min_ago > 3%` -> 触发 "火箭发射" 信号。
    *   **大单监测:** `Volume * Price > 1000万` -> 触发 "主力进场" 信号。
    *   **板块热度:** 统计全市场所有股票涨幅，按行业分类取平均 -> 实时热力图。

### 4.3 Notification (消息推送) - `nexus-notify`
*   **渠道:**
    *   WebSocket -> 前端弹窗 (High Priority)。
    *   Telegram/Feishu/DingTalk -> 移动端提醒 (Medium Priority)。
    *   Log -> 系统日志 (Low Priority)。

### 4.4 AI Copilot - `nexus-agent`
*   **职责:** 处理自然语言指令，调用后端 API，生成分析报告。
*   **核心流程:**
    1.  接收用户 Prompt ("帮我盯一下中信海直")。
    2.  Intent Recognition (意图识别) -> `Monitor_Stock`。
    3.  Parameter Extraction (参数提取) -> `stock="中信海直"`.
    4.  Action Execution (执行动作) -> 调用 `Analyzer.add_monitor("000099")`。
    5.  Response Generation (生成回复) -> "好的，已添加中信海直(000099)到监控列表，有异动会第一时间通知你。"

---

## 5. Development Phases (开发阶段)

### Phase 1: Infrastructure (基建)
*   搭建 Docker 环境 (Redis, PG, FastAPI)。
*   跑通 AkShare 数据获取 (Hello World)。

### Phase 2: Core Data (核心数据)
*   实现实时行情拉取与 Redis 缓存。
*   实现历史 K 线存储。

### Phase 3: Analysis Engine (分析引擎)
*   开发“异动精灵”算法。
*   计算“市场情绪”指标。

### Phase 4: Frontend & Visualization (前端与可视化)
*   画出 K 线图。
*   实现 WebSocket 实时弹窗。
*   集成 Dashboard。

---

## 6. Risks & Mitigation (风险与对策)

*   **Risk:** 数据接口被封 (Anti-Scraping)。
    *   **Mitigation:** 使用代理池 (Proxy Pool)；降低请求频率；多源切换。
*   **Risk:** 实时性不足 (Latency)。
    *   **Mitigation:** 优化 Redis 结构；使用异步 IO (asyncio)；仅仅推送变化的数据 (Delta)。
