# CryptoTracker 产品需求文档 (PRD)

> **版本**: 1.0
> **状态**: 已批准
> **最后更新**: 2026-08-21

---

## 1. 产品概述

CryptoTracker 是一个实时加密货币价格追踪与智能告警系统，通过 Binance WebSocket 提供毫秒级价格推送，结合 CoinGecko API 获取市场全景数据，支持自定义监控列表、K线图表、智能告警（价格阈值/涨跌幅/成交量异动）和策略回测（MA交叉/RSI/布林带），面向个人交易者和量化爱好者，零配置 `docker compose up` 即可启动全栈服务，**绝不触及用户资金、不提供投资建议**。

---

## 2. 目标用户与画像

### 画像 A：日内交易者小王

| 属性 | 描述 |
|------|------|
| 背景 | 28岁，兼职加密货币日内交易，主要交易 BTC/ETH/SOL |
| 痛点 | 在多个交易所之间切换看行情，错过突发价格异动 |
| 核心场景 | 设置 BTC 跌破 $58,000 时浏览器推送告警；查看 15 分钟 K 线确认趋势；用 MA 交叉策略回测验证自己的判断 |
| 成功标准 | 告警延迟 < 2 秒，K 线加载 < 1 秒 |

### 画像 B：量化爱好者阿明

| 属性 | 描述 |
|------|------|
| 背景 | 35岁，软件工程师，业余研究量化策略 |
| 痛点 | 缺少免费、开箱即用的回测环境，每次搭环境耗时数小时 |
| 核心场景 | docker compose up 启动后，选择 ETH 的历史 1h K 线，运行 RSI 超买超卖策略回测，查看胜率和最大回撤 |
| 成功标准 | 从 clone 到跑通回测 < 5 分钟 |

### 画像 C：技术学习者小李

| 属性 | 描述 |
|------|------|
| 背景 | 22岁，计算机专业在读，学习 WebSocket 和全栈开发 |
| 痛点 | 想找一个有真实数据流的项目作为学习参考 |
| 核心场景 | 注册账号后查看 Dashboard 了解系统全貌；查看实时价格跳动理解 WebSocket；修改告警阈值理解前后端交互 |
| 成功标准 | 代码结构清晰、文档完善、能独立扩展功能 |

---

## 3. 功能需求

### 3.1 用户认证模块 (Auth)

| ID | 功能 | 描述 |
|----|------|------|
| AUTH-01 | 用户注册 | 邮箱 + 密码 + 昵称注册，密码 ≥ 8 字符，bcrypt 哈希存储 |
| AUTH-02 | 用户登录 | 邮箱 + 密码登录，返回 JWT access_token (有效期 24h) |
| AUTH-03 | Token 刷新 | access_token 过期前可刷新，无需重新登录 |
| AUTH-04 | 登录频率限制 | 同一 IP 5 分钟内最多 10 次登录尝试 |
| AUTH-05 | 密码强度校验 | 至少 8 字符，含字母和数字 |

**接口契约**:
```
POST /api/v1/auth/register
  Request:  { email: EmailStr, password: str (min 8), name: str (min 1, max 100) }
  Response: { code: 0, data: { id, email, name, role, created_at }, message: "" }
  Errors:   409 邮箱已存在, 422 校验失败

POST /api/v1/auth/login
  Request:  { email: EmailStr, password: str }
  Response: { code: 0, data: { access_token, token_type: "bearer", expires_in, user: {id, email, name, role} }, message: "" }
  Errors:   401 密码错误, 422 校验失败
```

### 3.2 行情数据模块 (Market Data)

| ID | 功能 | 描述 |
|----|------|------|
| MKT-01 | Top 100 币种列表 | 返回市值排名前 100 的币种，含当前价格、市值、24h 涨跌幅 |
| MKT-02 | 实时价格推送 | 通过 WebSocket 推送用户关注币种的实时价格（Binance ticker） |
| MKT-03 | 单币详情 | 返回单个币种的详细信息（价格、市值、流通量、ATH、ATL） |
| MKT-04 | 数据源切换 | CoinGecko 作为主数据源（30 calls/min），Binance REST 作为补充 |

**数据更新频率**:
- CoinGecko 列表数据: 每 60 秒刷新一次
- Binance WebSocket 实时价格: 实时推送（~100ms 延迟）
- 缓存策略: Redis 缓存列表数据 60 秒

### 3.3 监控列表模块 (Watchlist)

| ID | 功能 | 描述 |
|----|------|------|
| WL-01 | 添加关注币种 | 已登录用户可将币种添加到监控列表（最多 50 个） |
| WL-02 | 移除关注币种 | 从监控列表移除 |
| WL-03 | 查看监控列表 | 返回用户的监控列表及各币种实时价格 |
| WL-04 | 默认排序 | 按添加时间倒序 |

**接口契约**:
```
GET    /api/v1/watchlist              → 返回用户监控列表（含实时价格）
POST   /api/v1/watchlist              → { coin_id: "bitcoin" }
DELETE /api/v1/watchlist/{coin_id}    → 移除
```

### 3.4 K 线图表模块 (Kline)

| ID | 功能 | 描述 |
|----|------|------|
| KL-01 | 获取 K 线数据 | 支持 1m/5m/15m/1h/4h/1d 六种时间周期 |
| KL-02 | 历史数据 | 每次返回最多 500 根 K 线 |
| KL-03 | 实时 K 线更新 | WebSocket 推送当前周期的 K 线更新 |
| KL-04 | 前端图表渲染 | 使用 TradingView Lightweight Charts 或 ECharts 渲染 |

**接口契约**:
```
GET /api/v1/coins/{coin_id}/klines?interval=1h&limit=200
  Response: { code: 0, data: { coin_id, symbol, interval, klines: [ { open_time, open, high, low, close, volume, close_time } ] } }

WebSocket /ws/kline/{symbol}/{interval}
  Push: { open_time, open, high, low, close, volume, is_closed }
```

### 3.5 智能告警模块 (Smart Alerts)

| ID | 功能 | 描述 |
|----|------|------|
| ALT-01 | 价格阈值告警 | 当价格突破/跌破指定值时触发 |
| ALT-02 | 涨跌幅告警 | 24h/1h 涨跌幅超过用户设定百分比时触发 |
| ALT-03 | 成交量异动告警 | 5 分钟成交量超过前 1 小时均值 N 倍时触发 |
| ALT-04 | WebSocket 推送 | 告警通过 WebSocket 实时推送到浏览器 |
| ALT-05 | 告警历史 | 记录所有已触发的告警，支持分页查询 |
| ALT-06 | 告警管理 | CRUD 操作，单用户最多 20 条活跃告警 |

**接口契约**:
```
POST /api/v1/alerts
  Request: {
    symbol: "BTCUSDT",
    type: "price_threshold" | "percent_change" | "volume_spike",
    condition: { direction: "above" | "below", value: 60000 }
  }

GET  /api/v1/alerts           → 用户的所有告警
GET  /api/v1/alerts/history   → 已触发告警历史
DELETE /api/v1/alerts/{id}    → 删除告警

WebSocket /ws/alerts
  Push: { alert_id, symbol, type, message, triggered_at, current_price }
```

### 3.6 策略回测模块 (Backtesting)

| ID | 功能 | 描述 |
|----|------|------|
| BT-01 | MA 均线交叉策略 | 短期 MA 上穿长期 MA 做多，下穿做空 |
| BT-02 | RSI 策略 | RSI < 30 做多，RSI > 70 做空 |
| BT-03 | 布林带策略 | 价格触及下轨做多，触及上轨做空 |
| BT-04 | 回测参数配置 | 用户可设定起止时间、初始资金、手续费率 |
| BT-05 | 回测结果 | 返回总收益率、胜率、最大回撤、夏普比率、交易次数 |
| BT-06 | 回测图表 | 前端展示净值曲线和买卖点标注 |

**接口契约**:
```
POST /api/v1/backtest
  Request: {
    symbol: "ETHUSDT",
    interval: "1h",
    strategy: "ma_cross",
    params: { short_period: 7, long_period: 25 },
    start_date: "2025-01-01",
    end_date: "2025-06-30",
    initial_capital: 10000,
    fee_rate: 0.001
  }
  Response: {
    code: 0,
    data: {
      total_return: 0.23,
      win_rate: 0.58,
      max_drawdown: 0.12,
      sharpe_ratio: 1.45,
      total_trades: 47,
      equity_curve: [...],
      trades: [{ entry_time, exit_time, side, entry_price, exit_price, pnl }]
    }
  }
```

### 3.7 仪表盘模块 (Dashboard)

| ID | 功能 | 描述 |
|----|------|------|
| DB-01 | 市场概览 | 显示 BTC 主导率、总市值、24h 总交易量、恐惧贪婪指数 |
| DB-02 | 监控列表摘要 | 用户关注币种的价格变动摘要 |
| DB-03 | 活跃告警状态 | 当前告警条件及距离触发的百分比 |
| DB-04 | 最近回测结果 | 最近 5 次回测的策略和收益 |

---

## 4. 用户故事 (Given/When/Then)

### 4.1 用户认证

**US-AUTH-01: 新用户注册**
```
Given 用户未注册
When  用户提交 POST /api/v1/auth/register { email: "trader@example.com", password: "Secure123", name: "小王" }
Then  返回 HTTP 200, code=0, 包含用户 id、email、name
And   数据库中存在该用户，password_hash 非明文
```

**US-AUTH-02: 重复注册**
```
Given 邮箱 "trader@example.com" 已注册
When  用户再次提交相同邮箱注册
Then  返回 HTTP 409, message 包含"邮箱已存在"
```

**US-AUTH-03: 登录成功**
```
Given 用户已注册且密码正确
When  用户提交 POST /api/v1/auth/login { email, password }
Then  返回 HTTP 200, data 包含 access_token 和 token_type="bearer"
And   token 解码后包含 user_id 和 exp 字段
```

### 4.2 行情数据

**US-MKT-01: 获取 Top 100 币种**
```
Given 用户已登录
When  用户请求 GET /api/v1/coins?page=1&page_size=100
Then  返回 HTTP 200, data.items 为数组且 len=100
And   每个元素包含 symbol, name, current_price, market_cap, price_change_pct_24h
```

**US-MKT-02: WebSocket 实时价格**
```
Given 用户已连接 WebSocket /ws/prices
When  Binance 推送 BTCUSDT 新价格
Then  客户端在 2 秒内收到 { symbol: "BTCUSDT", price: <新价格>, timestamp }
```

### 4.3 监控列表

**US-WL-01: 添加到监控列表**
```
Given 用户已登录，监控列表未满 50
When  用户提交 POST /api/v1/watchlist { coin_id: "ethereum" }
Then  返回 HTTP 200, 监控列表包含 ethereum
And   GET /api/v1/watchlist 返回中包含 ethereum 及其实时价格
```

**US-WL-02: 超出监控上限**
```
Given 用户监控列表已有 50 个币种
When  用户尝试添加第 51 个
Then  返回 HTTP 400, message 包含"监控列表已满"
```

### 4.4 K 线图表

**US-KL-01: 获取历史 K 线**
```
Given 用户已登录
When  用户请求 GET /api/v1/coins/bitcoin/klines?interval=1h&limit=200
Then  返回 HTTP 200, data.klines 数组长度 ≤ 200
And   每根 K 线包含 open_time, open, high, low, close, volume
And   K 线按 open_time 升序排列
```

**US-KL-02: 实时 K 线推送**
```
Given 用户已连接 WebSocket /ws/kline/BTCUSDT/1m
When  当前 1 分钟 K 线有新成交
Then  客户端收到更新的 OHLCV 数据，is_closed=false
When  1 分钟周期结束
Then  客户端收到 is_closed=true 的完整 K 线
```

### 4.5 智能告警

**US-ALT-01: 创建价格告警**
```
Given 用户已登录
When  用户提交 POST /api/v1/alerts { symbol: "BTCUSDT", type: "price_threshold", condition: { direction: "above", value: 70000 } }
Then  返回 HTTP 200, 包含 alert_id
And   GET /api/v1/alerts 返回中包含该告警
```

**US-ALT-02: 告警触发推送**
```
Given 用户有活跃告警: BTCUSDT > 70000
And   用户已连接 WebSocket /ws/alerts
When  BTCUSDT 价格首次突破 70000
Then  WebSocket 推送告警消息，包含 alert_id, symbol, current_price, triggered_at
And   该告警状态变为 triggered
And   告警写入历史记录
```

**US-ALT-03: 成交量异动检测**
```
Given 用户设置 ETHUSDT 成交量异动告警，倍数=3
When  最近 5 分钟成交量 ≥ 前 1 小时均值 × 3
Then  触发告警推送
```

### 4.6 策略回测

**US-BT-01: MA 交叉回测**
```
Given 用户已登录
When  用户提交 POST /api/v1/backtest { symbol: "ETHUSDT", interval: "1h", strategy: "ma_cross", params: { short_period: 7, long_period: 25 }, start_date: "2025-01-01", end_date: "2025-06-30", initial_capital: 10000, fee_rate: 0.001 }
Then  返回 HTTP 200
And   data 包含 total_return, win_rate, max_drawdown, sharpe_ratio, total_trades
And   total_trades > 0
And   equity_curve 为非空数组
```

**US-BT-02: 无效参数拒绝**
```
Given 用户已登录
When  用户提交回测请求，start_date > end_date
Then  返回 HTTP 422, message 包含参数校验错误信息
```

### 4.7 仪表盘

**US-DB-01: 查看市场概览**
```
Given 用户已登录
When  用户请求 GET /api/v1/dashboard/summary
Then  返回 HTTP 200
And   data 包含 total_market_cap, total_volume_24h, btc_dominance_pct
And   所有数值为正数
```

**US-DB-02: 告警状态摘要**
```
Given 用户有 3 条活跃告警
When  用户请求 GET /api/v1/dashboard/summary
Then  返回 HTTP 200
And   data 包含 user_active_alerts_count = 3
```

---

## 5. 非功能需求

### 5.1 性能

| 指标 | 目标 |
|------|------|
| API 响应时间 (P95) | < 200ms (不含回测) |
| 回测响应时间 (500 根 K 线) | < 3 秒 |
| WebSocket 推送延迟 | < 2 秒（从 Binance 收到到客户端显示） |
| 前端首屏加载 | < 3 秒（生产模式 nginx 静态服务） |
| 并发 WebSocket 连接 | ≥ 100 |
| CoinGecko API 调用 | ≤ 30 次/分钟（Redis 缓存兜底） |

### 5.2 安全

| 要求 | 实现 |
|------|------|
| 密码存储 | bcrypt 哈希，不可逆 |
| 认证 | JWT Bearer Token，所有写端点强制认证 |
| 输入校验 | Pydantic Schema 校验所有输入 |
| 频率限制 | 登录 10次/5min/IP，API 60次/min/user |
| 敏感信息 | API Key 不入日志，response 不含 password_hash |
| CORS | 仅允许前端域名 |
| SQL 注入 | SQLAlchemy ORM 参数化查询 |

### 5.3 部署

| 要求 | 实现 |
|------|------|
| 启动方式 | `docker compose up` 一键启动所有服务 |
| 服务编排 | backend + frontend + PostgreSQL + Redis + Celery worker |
| 环境变量 | 通过 .env 文件注入，不硬编码 |
| 健康检查 | GET /health 返回 200 |
| 数据持久化 | PostgreSQL 数据挂载 volume |
| 前端部署 | 多阶段构建 + nginx 静态服务 |
| 日志 | JSON 格式，stdout 输出 |

### 5.4 可维护性

| 要求 | 描述 |
|------|------|
| 代码结构 | Router → Service → CRUD → Model 分层 |
| 类型标注 | 所有函数有参数和返回类型标注 |
| 数据库迁移 | Alembic 管理 |
| 依赖管理 | requirements.txt 固定版本 |
| API 文档 | FastAPI 自动生成 Swagger (/docs) |

---

## 6. 验收标准（逐功能可测试）

### 6.1 认证模块
- [ ] `curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"Test1234","name":"测试用户"}'` → 200, 返回 user id
- [ ] 同一邮箱再次注册 → 409
- [ ] `curl -X POST http://localhost:8000/api/v1/auth/login -d '{"email":"test@test.com","password":"Test1234"}'` → 200, 返回 access_token
- [ ] 错误密码登录 → 401
- [ ] 无 Token 访问受保护端点 → 401

### 6.2 行情数据模块
- [ ] `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/coins?page_size=10` → 200, 返回 10 个币种
- [ ] 每个币种包含 symbol, current_price, market_cap, price_change_pct_24h 字段
- [ ] 60 秒内重复请求，响应来自缓存（响应时间 < 50ms）

### 6.3 监控列表模块
- [ ] POST /api/v1/watchlist { "coin_id": "bitcoin" } → 200
- [ ] GET /api/v1/watchlist → 包含刚添加的 bitcoin
- [ ] DELETE /api/v1/watchlist/bitcoin → 200
- [ ] GET /api/v1/watchlist → 不再包含 bitcoin

### 6.4 K 线模块
- [ ] `GET /api/v1/coins/bitcoin/klines?interval=1h&limit=100` → 200, 返回 100 根 K 线
- [ ] K 线字段完整: open_time, open, high, low, close, volume
- [ ] 无效 interval 参数 → 422

### 6.5 智能告警模块
- [ ] POST /api/v1/alerts 创建告警 → 200, 返回 alert_id
- [ ] GET /api/v1/alerts → 包含新创建的告警
- [ ] WebSocket 连接 /ws/alerts → 连接成功
- [ ] 告警触发时 WebSocket 收到推送消息
- [ ] DELETE /api/v1/alerts/{id} → 200

### 6.6 策略回测模块
- [ ] POST /api/v1/backtest (MA 交叉策略) → 200, 返回回测结果
- [ ] 结果包含 total_return, win_rate, max_drawdown, sharpe_ratio
- [ ] equity_curve 非空数组
- [ ] 无效日期范围 → 422

### 6.7 仪表盘模块
- [ ] GET /api/v1/dashboard/summary → 200, 包含市场概览数据
- [ ] 浏览器访问 http://localhost → 前端页面正常加载
- [ ] 登录后 Dashboard 显示监控列表和告警状态

### 6.8 部署验收
- [ ] `docker compose up -d` → 所有容器启动无报错
- [ ] `curl http://localhost:8000/health` → 200
- [ ] `docker compose logs backend` → 无 ERROR 级别日志
- [ ] 浏览器访问 http://localhost → 前端加载完成

---

## 7. 不在范围内 (Out of Scope)

以下功能**明确不做**，任何相关需求直接拒绝：

| 类别 | 不做的事 |
|------|---------|
| 交易 | 不接入交易 API、不执行买卖、不管理订单 |
| 钱包 | 不连接钱包、不存储私钥、不做链上分析 |
| 资金 | 不碰用户资金、不做资产管理、不做盈亏计算 |
| 投资建议 | 不提供买入/卖出建议、不做预测 |
| 社交 | 不做社区、不做跟单、不做排行榜 |
| 支付 | 不做付费功能、不做订阅 |
| 移动端 | 不做 iOS/Android 原生 App |
| 多语言 | MVP 仅中文界面 |
| 通知渠道 | 仅 WebSocket 浏览器推送，不做邮件/短信/Telegram |

---

## 8. 成功指标

| 指标 | 目标值 | 测量方式 |
|------|--------|---------|
| 启动到可用时间 | < 5 分钟 | 从 git clone 到 docker compose up 完成并通过健康检查 |
| API 响应成功率 | > 99% | 健康检查 + 端点监控 |
| WebSocket 连接稳定性 | 无断连 > 1 小时 | 客户端心跳监测 |
| 告警延迟 | < 2 秒 | 从价格变动到客户端收到推送的时间差 |
| 回测准确性 | 结果可复现 | 相同参数多次执行结果一致 |
| 代码覆盖率 | > 70% (核心模块) | pytest --cov |
| 安全漏洞 | 0 Critical/High | bandit + safety 扫描 |

---

## 附录：技术栈（参考）

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic |
| 异步任务 | Celery + Redis |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7 |
| 前端 | React 18 + Ant Design Pro + ECharts |
| 实时通信 | FastAPI WebSocket |
| 部署 | Docker Compose |
| 数据源 | CoinGecko Demo API + Binance Public WebSocket + Binance REST |

---

*本文档是 CryptoTracker 项目的唯一需求锚点。所有设计、开发、测试活动以此为准。*
