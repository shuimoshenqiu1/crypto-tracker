# CryptoTracker 架构设计文档

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose 集群                                 │
│                                                                                 │
│  ┌──────────┐    ┌──────────────────────────────────────────┐                   │
│  │  Nginx   │◄───│              Frontend (React)             │                   │
│  │  :80     │    │  - 市场总览 Dashboard                      │                   │
│  │          │    │  - K线图 (TradingView)                     │                   │
│  │  静态资源 │    │  - 自选列表 Watchlist                      │                   │
│  │  + 反代   │    │  - 告警管理 Alerts                         │                   │
│  └────┬─────┘    │  - 回测系统 Backtest                       │                   │
│       │          └──────────────────────────────────────────┘                   │
│       │ /api/v1/*                                                               │
│       │ /ws/*                                                                   │
│       ▼                                                                         │
│  ┌──────────────────────────────────────────┐                                   │
│  │         Backend (FastAPI)                 │                                   │
│  │  :8000                                   │                                   │
│  │  ┌─────────────┐  ┌──────────────────┐   │     ┌─────────────────┐           │
│  │  │ REST API    │  │ WebSocket Server │   │     │  Celery Worker  │           │
│  │  │ - Auth      │  │ - /ws/prices     │   │     │  - 价格同步      │           │
│  │  │ - Coins     │  │ - /ws/alerts     │   │     │  - 告警检测      │           │
│  │  │ - Watchlist │  │                  │   │     │  - 历史数据拉取  │           │
│  │  │ - Alerts    │  └───────┬──────────┘   │     │  - 回测执行      │           │
│  │  │ - Backtest  │          │              │     └────────┬────────┘           │
│  │  │ - Dashboard │          │              │              │                    │
│  │  └──────┬──────┘          │              │              │                    │
│  └─────────┼─────────────────┼──────────────┘              │                    │
│            │                 │                              │                    │
│            ▼                 ▼                              ▼                    │
│  ┌─────────────────┐  ┌─────────────────┐                                      │
│  │  PostgreSQL 15  │  │   Redis 7       │                                      │
│  │  :5432          │  │   :6379         │                                      │
│  │                 │  │                 │                                      │
│  │  - users        │  │  - 实时价格缓存  │                                      │
│  │  - coins        │  │  - Celery Broker │                                      │
│  │  - watchlists   │  │  - WS Pub/Sub   │                                      │
│  │  - alerts       │  │  - Session缓存   │                                      │
│  │  - klines       │  │                 │                                      │
│  │  - backtests    │  └─────────────────┘                                      │
│  └─────────────────┘                                                            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

        外部数据源
        ═══════════
        ┌───────────────────┐     ┌────────────────────────┐
        │ CoinGecko API     │     │ Binance                │
        │ (30 req/min)      │     │ - WebSocket (实时行情)   │
        │ - 币种元数据       │     │ - REST API (1200/min)  │
        │ - 市值/排名        │     │   - K线历史数据         │
        └───────────────────┘     └────────────────────────┘
```

---

## 2. 组件分解

### 2.1 Backend 服务层

| 模块 | 职责 | 关键技术 |
|------|------|----------|
| `auth` | 用户注册/登录/JWT签发 | passlib+bcrypt==4.0.1, python-jose |
| `coins` | 币种列表/详情/K线查询 | SQLAlchemy async, JSONB |
| `watchlist` | 用户自选管理 | 用户关联表 CRUD |
| `alerts` | 告警规则 CRUD + 历史记录 | Pydantic Schema 校验 |
| `backtest` | 回测任务提交/结果查询 | Celery async task |
| `dashboard` | 市场概览聚合 | Redis 缓存 + DB 聚合 |
| `websocket` | 实时推送(价格/告警) | FastAPI WebSocket + Redis Pub/Sub |

### 2.2 Celery 异步任务

| 任务 | 触发方式 | 频率 | 说明 |
|------|----------|------|------|
| `sync_coin_metadata` | Celery Beat | 每5分钟 | 从 CoinGecko 拉取币种元数据(市值、排名等) |
| `sync_realtime_prices` | 常驻进程 | 持续 | 维护 Binance WebSocket 连接，写入 Redis |
| `check_alert_rules` | Celery Beat | 每10秒 | 读 Redis 价格 → 匹配告警规则 → 触发通知 |
| `fetch_klines` | 按需/定时 | 按需 | 从 Binance REST 拉取历史K线写入 PostgreSQL |
| `run_backtest` | 用户触发 | 按需 | 执行回测策略，结果写入 DB |

### 2.3 Frontend 页面

| 页面 | 路由 | 核心组件 |
|------|------|----------|
| 登录/注册 | `/login`, `/register` | Ant Design Form |
| 市场总览 | `/dashboard` | 统计卡片 + 涨跌榜 |
| 币种列表 | `/coins` | ProTable (分页/排序/搜索) |
| 币种详情 | `/coins/:id` | TradingView K线图 + 基本信息 |
| 自选列表 | `/watchlist` | 可拖拽列表 + 实时价格 |
| 告警管理 | `/alerts` | 规则列表 + 创建弹窗 |
| 回测系统 | `/backtest` | 策略选择 + 参数配置 + 结果图表 |

### 2.4 数据层

- **PostgreSQL**: 持久化存储（用户、币种、K线、告警、回测）
- **Redis**: 
  - 实时价格缓存 (`price:{symbol}` → JSON, TTL 30s)
  - WebSocket Pub/Sub 通道 (`channel:prices`, `channel:alerts:{user_id}`)
  - Celery Broker + Result Backend
  - 登录频率限制 (`rate_limit:login:{ip}`)

---

## 3. 数据流图

### 3.1 实时价格流

```
Binance WebSocket          Celery Worker           Redis              Backend WS           Frontend
     │                         │                    │                    │                   │
     │──── 推送 ticker ────────►│                    │                    │                   │
     │                         │                    │                    │                   │
     │                         │── SET price:BTCUSDT │                    │                   │
     │                         │─────────────────────►│                    │                   │
     │                         │                    │                    │                   │
     │                         │── PUBLISH channel:prices                 │                   │
     │                         │─────────────────────►│                    │                   │
     │                         │                    │                    │                   │
     │                         │                    │── SUB message ─────►│                   │
     │                         │                    │                    │                   │
     │                         │                    │                    │── WS push ────────►│
     │                         │                    │                    │   (JSON frame)     │
     │                         │                    │                    │                   │
```

### 3.2 告警检测流

```
Celery Beat (每10秒)       Celery Worker           Redis            PostgreSQL         WebSocket
     │                         │                    │                   │                 │
     │── 触发 check_alerts ────►│                    │                   │                 │
     │                         │                    │                   │                 │
     │                         │── GET price:* ─────►│                   │                 │
     │                         │◄── 当前价格 ────────│                   │                 │
     │                         │                    │                   │                 │
     │                         │── 查询 active alerts ──────────────────►│                 │
     │                         │◄── 规则列表 ────────────────────────────│                 │
     │                         │                    │                   │                 │
     │                         │── [匹配成功]        │                   │                 │
     │                         │── INSERT alert_history ────────────────►│                 │
     │                         │                    │                   │                 │
     │                         │── PUBLISH channel:alerts:{uid} ────────►│                 │
     │                         │                    │                   │── push ─────────►│
     │                         │                    │                   │                 │
```

### 3.3 历史数据 & 回测流

```
用户提交回测          Backend API           Celery Worker        Binance REST       PostgreSQL
     │                   │                      │                   │                  │
     │── POST /backtest ─►│                      │                   │                  │
     │                   │── dispatch task ─────►│                   │                  │
     │◄── job_id ────────│                      │                   │                  │
     │                   │                      │                   │                  │
     │                   │                      │── 检查K线数据是否充足 ────────────────►│
     │                   │                      │◄── 缺失区间 ───────────────────────────│
     │                   │                      │                   │                  │
     │                   │                      │── GET /klines ────►│                  │
     │                   │                      │◄── OHLCV 数据 ────│                  │
     │                   │                      │                   │                  │
     │                   │                      │── INSERT klines ──────────────────────►│
     │                   │                      │                   │                  │
     │                   │                      │── 执行策略引擎 ──► [计算收益/信号]     │
     │                   │                      │                   │                  │
     │                   │                      │── UPDATE backtest_jobs (结果) ────────►│
     │                   │                      │                   │                  │
     │── GET /backtest/{id} ─►│                  │                   │                  │
     │◄── 结果 + 图表数据 ────│                  │                   │                  │
```

---

## 4. 数据库 Schema 设计

### 4.1 users 表

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'user',  -- 'user' | 'admin'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### 4.2 coins 表

```sql
CREATE TABLE coins (
    id              VARCHAR(100) PRIMARY KEY,  -- CoinGecko slug: 'bitcoin'
    symbol          VARCHAR(20) NOT NULL,       -- 'BTC'
    name            VARCHAR(200) NOT NULL,      -- 'Bitcoin'
    image_url       TEXT,
    market_cap      BIGINT,
    market_cap_rank INTEGER,
    current_price   NUMERIC(24, 8),
    price_change_24h        NUMERIC(24, 8),
    price_change_pct_24h    NUMERIC(10, 4),
    total_volume    BIGINT,
    circulating_supply      NUMERIC(24, 4),
    max_supply      NUMERIC(24, 4),
    ath             NUMERIC(24, 8),
    ath_date        TIMESTAMPTZ,
    extra           JSONB DEFAULT '{}',        -- 灵活存储额外字段
    binance_symbol  VARCHAR(20),               -- 'BTCUSDT' 对应的交易对
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_coins_symbol ON coins(symbol);
CREATE INDEX idx_coins_market_cap_rank ON coins(market_cap_rank);
CREATE INDEX idx_coins_binance_symbol ON coins(binance_symbol);
```

### 4.3 watchlists 表

```sql
CREATE TABLE watchlists (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coin_id     VARCHAR(100) NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, coin_id)
);

CREATE INDEX idx_watchlists_user_id ON watchlists(user_id);
```

### 4.4 alerts 表

```sql
CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coin_id         VARCHAR(100) NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    condition_type  VARCHAR(30) NOT NULL,  -- 'price_above' | 'price_below' | 'pct_change_above' | 'pct_change_below'
    threshold       NUMERIC(24, 8) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_repeating    BOOLEAN NOT NULL DEFAULT FALSE,  -- 是否重复触发
    cooldown_secs   INTEGER NOT NULL DEFAULT 3600,   -- 冷却时间(秒)
    last_triggered  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_coin_id ON alerts(coin_id);
CREATE INDEX idx_alerts_active ON alerts(is_active) WHERE is_active = TRUE;
```

### 4.5 alert_history 表

```sql
CREATE TABLE alert_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id        UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coin_id         VARCHAR(100) NOT NULL,
    trigger_price   NUMERIC(24, 8) NOT NULL,
    condition_type  VARCHAR(30) NOT NULL,
    threshold       NUMERIC(24, 8) NOT NULL,
    message         TEXT,
    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alert_history_user_id ON alert_history(user_id);
CREATE INDEX idx_alert_history_triggered_at ON alert_history(triggered_at);
CREATE INDEX idx_alert_history_alert_id ON alert_history(alert_id);
```

### 4.6 klines 表

```sql
CREATE TABLE klines (
    id              BIGSERIAL PRIMARY KEY,
    coin_id         VARCHAR(100) NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    symbol          VARCHAR(20) NOT NULL,       -- 'BTCUSDT'
    interval        VARCHAR(10) NOT NULL,       -- '1m' | '5m' | '15m' | '1h' | '4h' | '1d'
    open_time       BIGINT NOT NULL,            -- Unix ms
    open            NUMERIC(24, 8) NOT NULL,
    high            NUMERIC(24, 8) NOT NULL,
    low             NUMERIC(24, 8) NOT NULL,
    close           NUMERIC(24, 8) NOT NULL,
    volume          NUMERIC(24, 8) NOT NULL,
    close_time      BIGINT NOT NULL,            -- Unix ms
    quote_volume    NUMERIC(24, 8),
    trades_count    INTEGER,

    UNIQUE(symbol, interval, open_time)
);

CREATE INDEX idx_klines_symbol_interval_time ON klines(symbol, interval, open_time DESC);
CREATE INDEX idx_klines_coin_id ON klines(coin_id);
```

### 4.7 backtest_jobs 表

```sql
CREATE TABLE backtest_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coin_id         VARCHAR(100) NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    strategy_name   VARCHAR(50) NOT NULL,       -- 'ma_cross' | 'rsi' | 'bollinger'
    params          JSONB NOT NULL DEFAULT '{}', -- 策略参数
    interval        VARCHAR(10) NOT NULL DEFAULT '1h',
    start_time      BIGINT NOT NULL,            -- Unix ms
    end_time        BIGINT NOT NULL,            -- Unix ms
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending' | 'running' | 'completed' | 'failed'
    result          JSONB,                      -- 回测结果(收益率、交易次数、夏普比等)
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_backtest_jobs_user_id ON backtest_jobs(user_id);
CREATE INDEX idx_backtest_jobs_status ON backtest_jobs(status);
CREATE INDEX idx_backtest_jobs_created_at ON backtest_jobs(created_at DESC);
```

### 4.8 ER 关系图

```
users ──1:N──► watchlists ──N:1──► coins
  │                                   │
  │──1:N──► alerts ──N:1──────────────┘
  │              │
  │              └──1:N──► alert_history
  │
  └──1:N──► backtest_jobs ──N:1──► coins
                                      │
                               coins ──1:N──► klines
```

---

## 5. 技术决策记录 (ADR)

### ADR-001: 选择 FastAPI 作为后端框架

- **状态**: 已采纳
- **背景**: 需要高性能异步框架，支持 WebSocket，自动生成 API 文档
- **决策**: FastAPI 0.104+
- **理由**: 
  - 原生 async/await 支持，天然适配 I/O 密集场景（外部API调用、DB查询）
  - 内置 WebSocket 支持
  - Pydantic 自动校验 + OpenAPI 文档
  - 社区生态成熟，与 SQLAlchemy 2.0 async 集成良好
- **约束**: `redirect_slashes=False`（避免 307 重定向导致前端困惑）

### ADR-002: 选择 PostgreSQL + JSONB 而非 NoSQL

- **状态**: 已采纳
- **背景**: K线数据结构固定，但币种元数据字段可能随 CoinGecko 接口变化
- **决策**: PostgreSQL 15 + JSONB 字段用于灵活数据
- **理由**:
  - 结构化数据（users, alerts, klines）用 SQL 强约束
  - 半结构化数据（coins.extra, backtest_jobs.result）用 JSONB
  - 避免引入额外数据库，降低运维复杂度
  - PostgreSQL 的 JSONB 索引能力足够应对查询需求

### ADR-003: Redis 多角色复用

- **状态**: 已采纳
- **背景**: 需要实时缓存、消息队列、Pub/Sub 三种能力
- **决策**: 单 Redis 7 实例承担全部角色
- **理由**:
  - 项目规模不大，单实例足够
  - 通过 DB 编号隔离：db0=缓存, db1=Celery broker, db2=Celery result
  - Pub/Sub 用于 WebSocket 广播，无持久化需求
- **风险**: 单点故障，生产环境可升级为 Redis Cluster

### ADR-004: Celery 用于异步任务而非 asyncio background tasks

- **状态**: 已采纳
- **背景**: 回测计算可能耗时数十秒，不应阻塞 API 进程
- **决策**: Celery + Redis broker
- **理由**:
  - 独立 worker 进程，不影响 API 响应
  - Beat 调度器支持定时任务（价格同步、告警检测）
  - 支持任务重试、超时控制
  - 可独立扩缩容 worker 数量
- **约束**: Celery 任务内使用同步 DB Session（非 async）

### ADR-005: 前端状态管理选择 zustand

- **状态**: 已采纳
- **背景**: 需要管理 WebSocket 实时数据、用户认证状态、页面状态
- **决策**: zustand（替代 Redux/MobX）
- **理由**:
  - API 极简，学习成本低
  - 无 boilerplate（对比 Redux Toolkit 仍更轻量）
  - 支持 middleware（persist、devtools）
  - 与 React 18 concurrent mode 兼容

### ADR-006: 密码哈希方案

- **状态**: 已采纳
- **决策**: passlib[bcrypt] + bcrypt==4.0.1
- **理由**: passlib 1.7.x 与 bcrypt>=4.1 存在兼容性问题，锁定 bcrypt==4.0.1
- **约束**: requirements.txt 必须显式声明 `bcrypt==4.0.1`

---

## 6. 部署架构

### Docker Compose 服务拓扑

```yaml
services:
  nginx:        # 反向代理 + 前端静态文件
    port: 80 -> 80
    depends_on: [frontend, backend]

  frontend:     # React 构建产物 (nginx serve)
    build: ./frontend (multi-stage)
    # 无 command，使用 Dockerfile CMD

  backend:      # FastAPI + Uvicorn
    port: 8000 (internal)
    depends_on: [postgres, redis]
    env_file: .env

  celery-worker:  # Celery 消费者
    build: same as backend
    command: celery -A app.celery_app worker
    depends_on: [postgres, redis]
    env_file: .env  # 与 backend 一致

  celery-beat:    # 定时调度器
    build: same as backend
    command: celery -A app.celery_app beat
    depends_on: [redis]

  postgres:     # 数据库
    image: postgres:15-alpine
    port: 5432 (internal)
    volumes: pg_data:/var/lib/postgresql/data

  redis:        # 缓存 + 消息队列
    image: redis:7-alpine
    port: 6379 (internal)
    volumes: redis_data:/data
```

### 网络拓扑

```
外部访问 :80
    │
    ▼
┌─────────┐     /api/v1/*      ┌─────────┐
│  Nginx  │────────────────────►│ Backend │
│         │     /ws/*           │  :8000  │
│         │────────────────────►│         │
│         │                     └────┬────┘
│         │     /*                   │
│         │── 静态文件 serve          │
└─────────┘                     ┌────┴────┐
                                │   PG    │
                                │  Redis  │
                                └─────────┘
```

### 环境变量管理

```bash
# .env (通过 env_file 注入，不进 git)
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/cryptotracker
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
SECRET_KEY=<至少32字符随机字符串>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
COINGECKO_API_URL=https://api.coingecko.com/api/v3
BINANCE_WS_URL=wss://stream.binance.com:9443/ws
BINANCE_API_URL=https://api.binance.com/api/v3
```

---

## 7. 安全考量

### 7.1 认证与授权

| 措施 | 说明 |
|------|------|
| JWT Bearer Token | 所有写操作端点必须认证 |
| bcrypt 密码哈希 | passlib + bcrypt==4.0.1，cost=12 |
| 登录频率限制 | 同一 IP 5次/分钟，超限返回 429 |
| Token 有效期 | 24h，不支持刷新（MVP 简化） |
| 角色校验 | admin 端点检查 role 字段 |

### 7.2 输入校验

| 措施 | 说明 |
|------|------|
| Pydantic Schema | 所有请求体经过严格类型校验 |
| 路径参数白名单 | coin_id 限制为 `[a-z0-9-]` 格式 |
| 分页参数限制 | page_size 最大 100 |
| SQL 注入防护 | SQLAlchemy 参数化查询，禁止原生 SQL 拼接 |

### 7.3 数据保护

| 措施 | 说明 |
|------|------|
| password_hash 不返回 | 响应 Schema 排除敏感字段 |
| SECRET_KEY 不硬编码 | 通过环境变量注入 |
| 错误信息脱敏 | 生产环境不暴露堆栈/DB 错误详情 |
| CORS 白名单 | 只允许前端域名来源 |

### 7.4 外部 API 安全

| 措施 | 说明 |
|------|------|
| 请求频率控制 | CoinGecko 30/min, Binance 1200/min，代码内置计数器 |
| 超时设置 | 外部请求统一 10s timeout |
| 失败重试 | 指数退避，最多 3 次 |
| WebSocket 断线重连 | Binance WS 断开后 5s 自动重连 |

### 7.5 WebSocket 安全

| 措施 | 说明 |
|------|------|
| 连接认证 | WS 握手时验证 JWT（query param 或首条消息） |
| 心跳机制 | 30s ping/pong，超时断开 |
| 消息大小限制 | 单帧最大 64KB |
| 连接数限制 | 单用户最多 5 个 WS 连接 |
