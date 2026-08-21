# CryptoTracker API 接口规格文档

## 全局约定

### 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://localhost:8000/api/v1` |
| 协议 | HTTP/1.1 (Nginx 反代后为 HTTPS) |
| 内容类型 | `application/json` |
| 字段命名 | `snake_case` |
| 时间格式 | Unix 毫秒时间戳 |
| 币种 ID | CoinGecko slug (如 `bitcoin`, `ethereum`) |
| 交易对 | Binance symbol (如 `BTCUSDT`) |
| 认证方式 | `Authorization: Bearer <jwt_token>` |
| 路由约束 | `redirect_slashes=False`（无尾斜杠重定向） |

### 统一响应格式

**成功响应:**
```json
{
  "code": 0,
  "data": { ... },
  "message": ""
}
```

**错误响应:**
```json
{
  "code": 40001,
  "data": null,
  "message": "错误描述"
}
```

### 错误码规范

| 错误码 | HTTP Status | 含义 |
|--------|-------------|------|
| 0 | 200 | 成功 |
| 40001 | 400 | 请求参数错误 |
| 40101 | 401 | 未认证 / Token 过期 |
| 40301 | 403 | 权限不足 |
| 40401 | 404 | 资源不存在 |
| 40901 | 409 | 资源冲突（已存在） |
| 42201 | 422 | 字段校验失败 |
| 42901 | 429 | 请求频率超限 |
| 50001 | 500 | 服务器内部错误 |

### 分页约定

**请求参数:**
- `page`: 页码，从 1 开始，默认 1
- `page_size`: 每页数量，默认 20，最大 100

**响应格式:**
```json
{
  "code": 0,
  "data": {
    "items": [...],
    "total": 150,
    "page": 1,
    "page_size": 20
  },
  "message": ""
}
```

---

## 1. 认证模块 (Auth)

### 1.1 POST /api/v1/auth/register

**描述:** 用户注册

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Content-Type | application/json | ✅ |

**请求体:**
```json
{
  "email": "user@example.com",
  "password": "StrongP@ss123",
  "name": "张三"
}
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| email | string | EmailStr, 必填 | 用户邮箱(唯一) |
| password | string | min=8, max=72, 必填 | 密码(至少含一个大写+一个数字) |
| name | string | min=1, max=100, 必填 | 用户昵称 |

**成功响应 (201):**
```json
{
  "code": 0,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "张三",
    "role": "user",
    "created_at": 1724234400000
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 409 | 40901 | 邮箱已被注册 |
| 422 | 42201 | 密码不符合规则 / 邮箱格式错误 |

---

### 1.2 POST /api/v1/auth/login

**描述:** 用户登录，返回 JWT Token

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Content-Type | application/json | ✅ |

**请求体:**
```json
{
  "email": "user@example.com",
  "password": "StrongP@ss123"
}
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| email | string | EmailStr, 必填 | 登录邮箱 |
| password | string | 必填 | 登录密码 |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "张三",
      "role": "user"
    }
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 401 | 40101 | 邮箱或密码错误 |
| 429 | 42901 | 登录频率超限 (5次/分钟/IP) |

---

### 1.3 GET /api/v1/auth/me

**描述:** 获取当前登录用户信息

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "张三",
    "role": "user",
    "is_active": true,
    "created_at": 1724234400000
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 401 | 40101 | Token 无效或过期 |

---

## 2. 币种模块 (Coins)

### 2.1 GET /api/v1/coins

**描述:** 获取币种列表（分页 + 排序）

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**查询参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 (max 100) |
| sort_by | string | market_cap_rank | 排序字段: `market_cap_rank` / `price_change_pct_24h` / `total_volume` / `name` |
| sort_order | string | asc | `asc` / `desc` |
| search | string | - | 按名称/symbol 模糊搜索 |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin",
        "image_url": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
        "current_price": 67234.56,
        "market_cap": 1320000000000,
        "market_cap_rank": 1,
        "price_change_pct_24h": 2.34,
        "total_volume": 28000000000,
        "binance_symbol": "BTCUSDT"
      }
    ],
    "total": 250,
    "page": 1,
    "page_size": 20
  },
  "message": ""
}
```

---

### 2.2 GET /api/v1/coins/{coin_id}

**描述:** 获取币种详情（含实时价格）

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| coin_id | string | CoinGecko slug，如 `bitcoin` |

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "image_url": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
    "current_price": 67234.56,
    "market_cap": 1320000000000,
    "market_cap_rank": 1,
    "price_change_24h": 1534.23,
    "price_change_pct_24h": 2.34,
    "total_volume": 28000000000,
    "circulating_supply": 19600000,
    "max_supply": 21000000,
    "ath": 73750.07,
    "ath_date": 1710374400000,
    "binance_symbol": "BTCUSDT",
    "updated_at": 1724234400000
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 404 | 40401 | coin_id 不存在 |

---

### 2.3 GET /api/v1/coins/{coin_id}/klines

**描述:** 获取币种历史 K 线数据 (OHLCV)

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| coin_id | string | CoinGecko slug |

**查询参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| interval | string | 1h | K线周期: `1m` / `5m` / `15m` / `1h` / `4h` / `1d` |
| start_time | int | - | 起始时间 (Unix ms)，必填 |
| end_time | int | - | 结束时间 (Unix ms)，必填 |
| limit | int | 500 | 返回数量上限 (max 1500) |

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "coin_id": "bitcoin",
    "symbol": "BTCUSDT",
    "interval": "1h",
    "klines": [
      {
        "open_time": 1724230800000,
        "open": 67100.00,
        "high": 67350.00,
        "low": 67050.00,
        "close": 67234.56,
        "volume": 1234.567,
        "close_time": 1724234399999,
        "quote_volume": 82945678.12,
        "trades_count": 45678
      }
    ]
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 400 | 40001 | start_time >= end_time / interval 无效 |
| 404 | 40401 | coin_id 不存在或无 Binance 交易对 |

---

## 3. 自选列表模块 (Watchlist)

### 3.1 GET /api/v1/watchlist

**描述:** 获取当前用户的自选列表

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "coin_id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin",
        "image_url": "https://...",
        "current_price": 67234.56,
        "price_change_pct_24h": 2.34,
        "sort_order": 0,
        "added_at": 1724234400000
      },
      {
        "coin_id": "ethereum",
        "symbol": "ETH",
        "name": "Ethereum",
        "image_url": "https://...",
        "current_price": 3456.78,
        "price_change_pct_24h": -1.23,
        "sort_order": 1,
        "added_at": 1724234500000
      }
    ],
    "total": 2
  },
  "message": ""
}
```

---

### 3.2 POST /api/v1/watchlist

**描述:** 添加币种到自选

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |
| Content-Type | application/json | ✅ |

**请求体:**
```json
{
  "coin_id": "bitcoin"
}
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| coin_id | string | 必填, 需存在于 coins 表 | CoinGecko slug |

**成功响应 (201):**
```json
{
  "code": 0,
  "data": {
    "coin_id": "bitcoin",
    "sort_order": 0,
    "added_at": 1724234400000
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 404 | 40401 | coin_id 不存在 |
| 409 | 40901 | 已在自选中 |

---

### 3.3 DELETE /api/v1/watchlist/{coin_id}

**描述:** 从自选中移除币种

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| coin_id | string | CoinGecko slug |

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": null,
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 404 | 40401 | 该币种不在自选中 |

---

## 4. 告警模块 (Alerts)

### 4.1 GET /api/v1/alerts

**描述:** 获取当前用户的告警规则列表

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**查询参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| is_active | bool | - | 筛选激活状态 |
| coin_id | string | - | 按币种筛选 |
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "alert-uuid-001",
        "coin_id": "bitcoin",
        "coin_symbol": "BTC",
        "coin_name": "Bitcoin",
        "condition_type": "price_above",
        "threshold": 70000.00,
        "is_active": true,
        "is_repeating": false,
        "cooldown_secs": 3600,
        "last_triggered": null,
        "created_at": 1724234400000,
        "updated_at": 1724234400000
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  },
  "message": ""
}
```

---

### 4.2 POST /api/v1/alerts

**描述:** 创建告警规则

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |
| Content-Type | application/json | ✅ |

**请求体:**
```json
{
  "coin_id": "bitcoin",
  "condition_type": "price_above",
  "threshold": 70000.00,
  "is_repeating": false,
  "cooldown_secs": 3600
}
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| coin_id | string | 必填 | CoinGecko slug |
| condition_type | string | 必填, enum | `price_above` / `price_below` / `pct_change_above` / `pct_change_below` |
| threshold | number | 必填, >0 | 触发阈值（价格类为 USD 价格，百分比类为百分比值如 5.0 表示 5%） |
| is_repeating | bool | 可选, default=false | 是否重复触发 |
| cooldown_secs | int | 可选, default=3600, min=60 | 重复触发冷却时间(秒) |

**成功响应 (201):**
```json
{
  "code": 0,
  "data": {
    "id": "alert-uuid-001",
    "coin_id": "bitcoin",
    "condition_type": "price_above",
    "threshold": 70000.00,
    "is_active": true,
    "is_repeating": false,
    "cooldown_secs": 3600,
    "created_at": 1724234400000
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 404 | 40401 | coin_id 不存在 |
| 422 | 42201 | condition_type 无效 / threshold <= 0 |

---

### 4.3 PATCH /api/v1/alerts/{alert_id}

**描述:** 更新告警规则（部分更新）

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| alert_id | string (UUID) | 告警 ID |

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |
| Content-Type | application/json | ✅ |

**请求体 (所有字段可选):**
```json
{
  "threshold": 75000.00,
  "is_active": false,
  "is_repeating": true,
  "cooldown_secs": 7200
}
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| threshold | number | >0 | 新阈值 |
| is_active | bool | - | 激活/静默 |
| is_repeating | bool | - | 是否重复触发 |
| cooldown_secs | int | min=60 | 冷却时间 |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "id": "alert-uuid-001",
    "coin_id": "bitcoin",
    "condition_type": "price_above",
    "threshold": 75000.00,
    "is_active": false,
    "is_repeating": true,
    "cooldown_secs": 7200,
    "updated_at": 1724238000000
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 403 | 40301 | 非本人告警 |
| 404 | 40401 | alert_id 不存在 |

---

### 4.4 DELETE /api/v1/alerts/{alert_id}

**描述:** 删除告警规则

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| alert_id | string (UUID) | 告警 ID |

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": null,
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 403 | 40301 | 非本人告警 |
| 404 | 40401 | alert_id 不存在 |

---

### 4.5 GET /api/v1/alerts/history

**描述:** 获取已触发告警的历史记录

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**查询参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| coin_id | string | - | 按币种筛选 |
| start_time | int | - | 起始时间 (Unix ms) |
| end_time | int | - | 结束时间 (Unix ms) |
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "history-uuid-001",
        "alert_id": "alert-uuid-001",
        "coin_id": "bitcoin",
        "coin_symbol": "BTC",
        "condition_type": "price_above",
        "threshold": 70000.00,
        "trigger_price": 70123.45,
        "message": "BTC 价格突破 $70,000.00，当前价格 $70,123.45",
        "triggered_at": 1724238000000
      }
    ],
    "total": 12,
    "page": 1,
    "page_size": 20
  },
  "message": ""
}
```

---

## 5. 回测模块 (Backtest)

### 5.1 POST /api/v1/backtest/run

**描述:** 提交回测任务（异步执行）

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |
| Content-Type | application/json | ✅ |

**请求体:**
```json
{
  "coin_id": "bitcoin",
  "strategy_name": "ma_cross",
  "params": {
    "short_period": 7,
    "long_period": 25
  },
  "interval": "1h",
  "start_time": 1721642400000,
  "end_time": 1724234400000
}
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| coin_id | string | 必填 | CoinGecko slug |
| strategy_name | string | 必填, enum | 策略名（见 5.3 strategies 列表） |
| params | object | 必填 | 策略参数（不同策略参数不同） |
| interval | string | 可选, default="1h" | K线周期 |
| start_time | int | 必填, Unix ms | 回测起始时间 |
| end_time | int | 必填, Unix ms | 回测结束时间 |

**成功响应 (202):**
```json
{
  "code": 0,
  "data": {
    "job_id": "backtest-uuid-001",
    "status": "pending",
    "created_at": 1724234400000
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 400 | 40001 | 时间范围无效 / 策略名无效 |
| 404 | 40401 | coin_id 不存在 |
| 422 | 42201 | 策略参数不匹配 |

---

### 5.2 GET /api/v1/backtest/{job_id}

**描述:** 查询回测任务结果

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| job_id | string (UUID) | 回测任务 ID |

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200) — 任务完成:**
```json
{
  "code": 0,
  "data": {
    "job_id": "backtest-uuid-001",
    "coin_id": "bitcoin",
    "strategy_name": "ma_cross",
    "params": {
      "short_period": 7,
      "long_period": 25
    },
    "interval": "1h",
    "start_time": 1721642400000,
    "end_time": 1724234400000,
    "status": "completed",
    "result": {
      "total_return_pct": 12.34,
      "annualized_return_pct": 45.67,
      "max_drawdown_pct": -8.92,
      "sharpe_ratio": 1.85,
      "total_trades": 23,
      "win_rate_pct": 60.87,
      "profit_factor": 2.13,
      "avg_holding_hours": 18.5,
      "trades": [
        {
          "type": "buy",
          "price": 64500.00,
          "time": 1721728800000,
          "quantity": 1.0
        },
        {
          "type": "sell",
          "price": 66200.00,
          "time": 1721815200000,
          "quantity": 1.0
        }
      ],
      "equity_curve": [
        {"time": 1721642400000, "value": 10000.00},
        {"time": 1721728800000, "value": 10234.56}
      ]
    },
    "created_at": 1724234400000,
    "completed_at": 1724234450000
  },
  "message": ""
}
```

**成功响应 (200) — 任务执行中:**
```json
{
  "code": 0,
  "data": {
    "job_id": "backtest-uuid-001",
    "status": "running",
    "result": null,
    "created_at": 1724234400000,
    "completed_at": null
  },
  "message": ""
}
```

**成功响应 (200) — 任务失败:**
```json
{
  "code": 0,
  "data": {
    "job_id": "backtest-uuid-001",
    "status": "failed",
    "result": null,
    "error_message": "历史数据不足，无法完成回测",
    "created_at": 1724234400000,
    "completed_at": 1724234430000
  },
  "message": ""
}
```

**错误响应:**
| Status | Code | 场景 |
|--------|------|------|
| 403 | 40301 | 非本人任务 |
| 404 | 40401 | job_id 不存在 |

---

### 5.3 GET /api/v1/backtest/strategies

**描述:** 获取可用回测策略列表及其参数说明

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "strategies": [
      {
        "name": "ma_cross",
        "display_name": "均线交叉策略",
        "description": "短期均线上穿长期均线时买入，下穿时卖出",
        "params_schema": {
          "short_period": {"type": "int", "min": 2, "max": 50, "default": 7, "description": "短期均线周期"},
          "long_period": {"type": "int", "min": 10, "max": 200, "default": 25, "description": "长期均线周期"}
        }
      },
      {
        "name": "rsi",
        "display_name": "RSI 超买超卖策略",
        "description": "RSI 低于超卖线买入，高于超买线卖出",
        "params_schema": {
          "period": {"type": "int", "min": 5, "max": 50, "default": 14, "description": "RSI 计算周期"},
          "oversold": {"type": "float", "min": 10, "max": 40, "default": 30, "description": "超卖阈值"},
          "overbought": {"type": "float", "min": 60, "max": 90, "default": 70, "description": "超买阈值"}
        }
      },
      {
        "name": "bollinger",
        "display_name": "布林带策略",
        "description": "价格触及下轨买入，触及上轨卖出",
        "params_schema": {
          "period": {"type": "int", "min": 10, "max": 50, "default": 20, "description": "布林带周期"},
          "std_dev": {"type": "float", "min": 1.0, "max": 3.0, "default": 2.0, "description": "标准差倍数"}
        }
      }
    ]
  },
  "message": ""
}
```

---

## 6. WebSocket 接口

### 6.1 WS /ws/prices

**描述:** 实时价格订阅

**连接方式:**
```
ws://localhost:8000/ws/prices?token={jwt_token}
```

**认证:** JWT Token 通过 query param `token` 传递

**客户端 → 服务端 (订阅消息):**
```json
{
  "action": "subscribe",
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
}
```

```json
{
  "action": "unsubscribe",
  "symbols": ["SOLUSDT"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| action | string | `subscribe` / `unsubscribe` |
| symbols | string[] | Binance 交易对列表 |

**服务端 → 客户端 (价格推送):**
```json
{
  "type": "price_update",
  "data": {
    "symbol": "BTCUSDT",
    "price": 67234.56,
    "price_change_pct_24h": 2.34,
    "volume_24h": 28000000000,
    "timestamp": 1724234400000
  }
}
```

**心跳:**
- 服务端每 30s 发送 `{"type": "ping"}`
- 客户端必须回复 `{"type": "pong"}`
- 60s 无 pong = 断开连接

**错误消息:**
```json
{
  "type": "error",
  "code": 40101,
  "message": "Token 已过期"
}
```

---

### 6.2 WS /ws/alerts

**描述:** 实时告警通知推送

**连接方式:**
```
ws://localhost:8000/ws/alerts?token={jwt_token}
```

**认证:** JWT Token 通过 query param `token` 传递

**服务端 → 客户端 (告警触发推送):**
```json
{
  "type": "alert_triggered",
  "data": {
    "alert_id": "alert-uuid-001",
    "coin_id": "bitcoin",
    "coin_symbol": "BTC",
    "condition_type": "price_above",
    "threshold": 70000.00,
    "trigger_price": 70123.45,
    "message": "BTC 价格突破 $70,000.00，当前价格 $70,123.45",
    "triggered_at": 1724238000000
  }
}
```

**心跳:** 同 /ws/prices

**说明:**
- 连接后自动接收该用户的所有告警通知
- 无需额外订阅操作
- 告警由 Celery worker 通过 Redis Pub/Sub 推送

---

## 7. Dashboard 模块

### 7.1 GET /api/v1/dashboard/summary

**描述:** 获取市场概览统计数据

**请求头:**
| Header | 值 | 必填 |
|--------|-----|------|
| Authorization | Bearer {token} | ✅ |

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "total_market_cap": 2450000000000,
    "total_volume_24h": 85000000000,
    "btc_dominance_pct": 53.8,
    "active_coins_count": 250,
    "top_gainers": [
      {
        "coin_id": "solana",
        "symbol": "SOL",
        "name": "Solana",
        "price_change_pct_24h": 15.67,
        "current_price": 178.90
      }
    ],
    "top_losers": [
      {
        "coin_id": "dogecoin",
        "symbol": "DOGE",
        "name": "Dogecoin",
        "price_change_pct_24h": -8.45,
        "current_price": 0.1234
      }
    ],
    "user_watchlist_count": 5,
    "user_active_alerts_count": 3,
    "updated_at": 1724234400000
  },
  "message": ""
}
```

---

## 8. Health 健康检查

### 8.1 GET /api/v1/health

**描述:** 服务健康检查（无需认证）

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "services": {
      "database": "connected",
      "redis": "connected",
      "celery": "active"
    },
    "timestamp": 1724234400000
  },
  "message": ""
}
```

**降级响应 (200，部分服务异常):**
```json
{
  "code": 0,
  "data": {
    "status": "degraded",
    "version": "1.0.0",
    "services": {
      "database": "connected",
      "redis": "disconnected",
      "celery": "inactive"
    },
    "timestamp": 1724234400000
  },
  "message": "部分服务不可用"
}
```

---

## 附录 A: JWT Token 结构

**Payload:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "role": "user",
  "exp": 1724320800,
  "iat": 1724234400
}
```

| 字段 | 说明 |
|------|------|
| sub | 用户 UUID |
| email | 用户邮箱 |
| role | 用户角色 (`user` / `admin`) |
| exp | 过期时间 (Unix 秒) |
| iat | 签发时间 (Unix 秒) |

---

## 附录 B: 告警条件类型说明

| condition_type | 触发条件 | threshold 含义 |
|----------------|----------|----------------|
| `price_above` | 当前价格 > threshold | USD 价格 |
| `price_below` | 当前价格 < threshold | USD 价格 |
| `pct_change_above` | 24h涨幅 > threshold | 百分比 (如 5.0 = 5%) |
| `pct_change_below` | 24h跌幅 < -threshold | 百分比 (如 5.0 = -5%) |

---

## 附录 C: 回测结果字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| total_return_pct | float | 总收益率 (%) |
| annualized_return_pct | float | 年化收益率 (%) |
| max_drawdown_pct | float | 最大回撤 (%) |
| sharpe_ratio | float | 夏普比率 |
| total_trades | int | 总交易次数 |
| win_rate_pct | float | 胜率 (%) |
| profit_factor | float | 盈亏比 |
| avg_holding_hours | float | 平均持仓时长 (小时) |
| trades | array | 交易记录列表 |
| equity_curve | array | 权益曲线数据点 |
