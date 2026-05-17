---
name: api-design
description: API设计规范 — RESTful设计、错误处理、分页、版本管理、安全性、Webhook、GraphQL对比、文档生成、限流熔断。
triggers:
  - "设计新的API接口"
  - "重构现有API"
  - "API breaking change"
  - "需要统一API风格"
  - "API文档不规范"
  - "设计Webhook"
  - "API限流熔断"
version: 1.0.0
---

# API Design

## Overview

API是系统间的契约。好的API设计：自描述、一致、安全、易调试。坏的API设计：让调用方痛苦、让修改困难、让文档成为谎言。

## When to Use

- 设计任何新的HTTP API
- 重构现有API接口
- 任何涉及客户端-服务端通信的功能
- 任何需要对外暴露接口的场景
- API breaking change前
- 设计事件驱动架构（Webhook）
- 需要在REST和GraphQL之间做选型

---

## Phase 1: RESTful基础

### 1.1 HTTP方法

| 方法 | 语义 | 幂等 | 安全 | 典型用途 |
|------|------|------|------|----------|
| GET | 读取资源 | ✓ | ✓ | 获取列表/详情 |
| POST | 创建资源 | ✗ | ✗ | 创建实体 |
| PUT | 完整替换 | ✓ | ✗ | 替换整个资源 |
| PATCH | 部分更新 | ✗ | ✗ | 更新部分字段 |
| DELETE | 删除资源 | ✓ | ✗ | 删除实体 |

### 1.2 URL设计

```
✓ GET /users                  用户列表
✓ GET /users/123             用户详情
✓ POST /users                 创建用户
✓ PUT /users/123             更新用户
✓ PATCH /users/123           部分更新
✓ DELETE /users/123          删除用户
✓ GET /users/123/orders       用户订单

✗ GET /getUsers
✗ POST /createUser
✗ /api/get_data.php
✗ /users/123/orders/456/items/789/payments   嵌套过深
```

### 1.3 嵌套资源规范

- 推荐嵌套深度：最多2层 `/users/123/orders`
- 跨资源关联用query参数：`GET /orders?user_id=123`
- 嵌套资源应是父资源的强从属关系
- 避免超过3层嵌套

### 1.4 命名规范

- 小写+下划线或中划线（`/user-orders` 或 `/user_orders`）
- 集合用复数名词：`/users`, `/orders`
- 具体名称避免泛型：`/invoice-items` 而非 `/items`
- 动作如无法映射到CRUD，用行为命名：`/users/123/activate`

---

## Phase 2: 请求与响应

### 2.1 请求格式

- 数据格式：JSON（`Content-Type: application/json`）
- 日期格式：ISO 8601（`2024-01-15T10:30:00Z`）
- 时间戳：Unix毫秒或ISO 8601
- 金额：最小单位（分）并在字段名标注，或用字符串避免浮点精度问题
- 布尔值：true/false（不用 1/0）
- null vs 空数组：`null`表示"未知/不适用"，`[]`表示"已确认无数据"

### 2.2 标准响应格式

**成功响应：**
```json
{
  "data": { },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "request_id": "req_abc123"
  }
}
```

**集合响应：**
```json
{
  "data": [
    { "id": "1", "name": "张三" },
    { "id": "2", "name": "李四" }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "has_next": true
  }
}
```

**错误响应：**
```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "用户不存在",
    "request_id": "req_abc123",
    "details": {}
  }
}
```

### 2.3 分页设计

**偏移分页（适合小数据量）：**
```
GET /users?page=1&page_size=20
```
- 适用场景：数据量<10万，用户需要跳转页码
- 缺点：数据变更时页码可能重复或跳跃

**光标分页（推荐，适合大数据量）：**
```
GET /users?cursor=eyJpZCI6IjEyMyJ9&page_size=20
```
- 适用场景：实时数据、无限滚动
- 优点：稳定的光标位置，不受数据变更影响
- 光标内容：Base64编码的 `{last_id, created_at}`

**响应元数据：**
```json
{
  "meta": {
    "total": 1000,
    "page_size": 20,
    "has_next": true,
    "has_prev": false,
    "next_cursor": "eyJpZCI6IjMifQ==",
    "prev_cursor": null
  }
}
```

---

## Phase 3: 错误处理

### 3.1 HTTP状态码规范

```
4xx 客户端错误
400 Bad Request          请求语法/格式错误
401 Unauthorized         未认证（未提供凭证）
403 Forbidden            已认证但无权限
404 Not Found            资源不存在
409 Conflict             资源冲突（重复创建、版本冲突）
410 Gone                 资源已永久删除
415 Unsupported Media    不支持的Content-Type
422 Unprocessable Entity 业务逻辑错误（验证失败）
429 Too Many Requests    请求频率超限

5xx 服务端错误
500 Internal Server Error    服务器内部错误
502 Bad Gateway              上游服务错误
503 Service Unavailable      服务不可用（临时过载）
504 Gateway Timeout          上游超时
```

### 3.2 错误码体系设计

错误码 = 领域(2字符) + 编号(4位数字)

```
US  用户相关   US0001 用户不存在
OR  订单相关   OR0001 订单不存在
PA  支付相关   PA0001 支付失败
SY  系统相关   SY0001 系统内部错误
```

### 3.3 错误响应规范

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求验证失败",
    "request_id": "req_abc123xyz",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确",
        "value": "not-an-email"
      },
      {
        "field": "age",
        "message": "年龄必须在0-150之间",
        "value": -5
      }
    ]
  }
}
```

### 3.4 错误处理原则

- **不暴露内部细节**：堆栈、SQL、服务器路径只记录日志
- **request_id贯穿始终**：客户端报此ID，服务器日志可查完整链路
- **面向用户的消息 vs 面向开发者的日志**：API返回通用消息，详情存日志
- **错误码供程序判断**：错误消息供人类阅读
- **429响应必须含Retry-After**：让客户端知道等多久

---

## Phase 4: 版本管理

### 4.1 版本策略对比

| 策略 | 格式 | 优点 | 缺点 |
|------|------|------|------|
| URL路径 | `/api/v1/users` | 直观、易调试、易缓存 | 改URL看起来"丑" |
| Header | `Accept: application/vnd.api+json; version=1` | URL干净 | 需要客户端处理特殊Header |
| Query参数 | `/users?version=1` | 灵活 | 容易被忽略、缓存困难 |

**推荐：URL路径版本**（`/api/v1/users`）

### 4.2 Breaking Change 定义

以下变更属于Breaking Change，需要升级Major版本：

- 删除字段
- 删除API端点
- 改变字段类型
- 改变字段语义（`status: 0=创建中` 改为 `0=已取消`）
- 改变必需性（可选→必选）
- 改变认证/授权要求
- 改变响应结构
- 改变HTTP状态码语义

### 4.3 Non-Breaking Change

以下变更可以以Minor/Patch版本发布：

- 新增可选字段
- 新增API端点
- 新增可选query参数
- 新增可选header
- 新增枚举值（客户端需忽略未知值）

### 4.4 版本生命周期

```
Major.Minor.Patch
1.2.3
│ │ │
│ │ └─ Patch: 修复bug，完全向后兼容
│ └─── Minor: 新功能，向后兼容
└───── Major: Breaking Change
```

建议：
- 生产环境至少支持最近2个Minor版本
- Breaking Change至少提前1个版本公告Deprecation
- 废弃周期：建议6-12个月

### 4.5 Deprecation 机制

**响应中标记废弃字段：**
```json
{
  "data": {
    "id": "123",
    "name": "张三",
    "email": "zhang@example.com",
    "_deprecated": {
      "email": {
        "deprecated_at": "2024-06-01",
        "removed_in": "v3.0",
        "use_instead": "contact_email"
      }
    },
    "contact_email": "zhang@example.com"
  }
}
```

**在Response Header中宣告：**
```http
Deprecation: true
Sunset: Sat, 01 Jun 2024 00:00:00 GMT
Link: <https://api.example.com/docs/v3>; rel="successor-version"
```

**废弃API端点返回警告：**
```json
{
  "data": {...},
  "warnings": [
    {
      "code": "DEPRECATED_ENDPOINT",
      "message": "此端点将于2024-12-01废弃，请迁移到 /v2/users",
      "sunset_date": "2024-12-01"
    }
  ]
}
```

---

## Phase 5: 安全

### 5.1 认证

- **Bearer Token（JWT）**：`Authorization: Bearer <token>`
- **API Key**：`X-API-Key: <key>`（用于服务端到服务端）
- **OAuth 2.0**：第三方授权

**禁止：**
- Token放在URL中（会被日志、浏览器历史记录暴露）
- Basic Auth（除非全程HTTPS）

### 5.2 授权

- 资源所有者验证：用户只能访问自己的资源
- 权限模型：`角色-权限`映射或`资源-操作`矩阵
- 字段级授权：某些字段对某些角色隐藏

```json
{
  "data": {
    "id": "123",
    "name": "张三",
    "email": "zhang@example.com",   // 仅owner可见
    "is_admin": false                // 仅admin角色可见
  },
  "meta": {
    "visible_fields": ["id", "name", "email"]
  }
}
```

### 5.3 输入验证

- 白名单验证：类型、范围、格式、长度
- SQL注入防护：参数化查询
- XSS防护：输出编码
- 批量操作限制：单次请求不超过100条（可配置）

---

## Phase 6: Webhook设计

### 6.1 Webhook vs API对比

| 维度 | REST API (拉) | Webhook (推) |
|------|---------------|--------------|
| 方向 | 客户端发起请求 | 服务端主动推送 |
| 实时性 | 轮询，有延迟 | 事件触发，即时 |
| 复杂度 | 简单 | 复杂（重试、幂等） |
| 资源消耗 | 客户端持续轮询 | 仅服务端有消耗 |
| 适用场景 | 请求-响应模型 | 异步事件通知 |

### 6.2 Webhook设计原则

**事件命名：**
```
<resource>.<action>
├── user.created          用户创建
├── user.updated          用户更新
├── user.deleted          用户删除
├── order.paid            订单已支付
├── order.completed       订单已完成
├── payment.failed        支付失败
└── subscription.cancelled 订阅取消
```

**Payload设计：**
```json
{
  "id": "evt_01HXYZ123",
  "type": "order.paid",
  "created_at": "2024-01-15T10:30:00Z",
  "data": {
    "id": "ord_789",
    "user_id": "usr_123",
    "amount": 19900,
    "currency": "CNY",
    "paid_at": "2024-01-15T10:29:55Z"
  },
  "metadata": {
    "order_source": "mobile_app"
  }
}
```

### 6.3 安全机制

**签名验证（必选）：**
```http
X-Webhook-Signature: sha256=abc123...
X-Webhook-Timestamp: 1705312800
```

验证流程：
1. 提取Timestamp，检查是否在5分钟窗口内（防重放）
2. 拼接 `timestamp + "." + payload` 用秘钥计算HMAC
3. 用constant-time comparison比对签名

```python
# 示例签名验证
import hmac
import hashlib

def verify_signature(payload: bytes, timestamp: str, signature: str, secret: str) -> bool:
    if abs(time.time() - int(timestamp)) > 300:
        return False  # 重放攻击
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

**IP白名单（推荐）：**
- 只允许来自已知IP段的webhook调用
- 维护IP列表并定期更新

### 6.4 可靠性设计

**重试机制：**
- 使用指数退避：1s → 2s → 4s → 8s → 16s → 32s（最大）
- 总重试次数：建议5-7次
- 超时时间：建议30秒
- 成功后返回2xx

**幂等性（必选）：**
```json
{
  "id": "evt_01HXYZ123",
  "idempotency_key": "pay_123_user_456"  // 唯一键用于去重
}
```

- 接收方根据 `idempotency_key` 做去重
- 建议保留时间：至少24小时
- 客户端可使用 `X-Idempotency-Key` 手动指定

**事件顺序：**
- 事件可能乱序到达
- 使用 `created_at` 或序列号做排序
- 接收方处理时考虑幂等和乱序

### 6.5 Webhook端点设计

**注册机制：**
```json
{
  "url": "https://client.example.com/webhooks/orders",
  "events": ["order.created", "order.paid", "order.cancelled"],
  "secret": "whsec_xxx",
  "active": true
}
```

**禁用端点响应：**
```http
POST /webhooks/orders
HTTP/1.1 410 Gone
X-Webhook-Disabled-Reason: Subscription expired
```

**超时处理：**
- 服务端30秒无响应 → 记录失败并重试
- 客户端超时应返回立即失败，不要等

### 6.6 测试Webhook

- 使用 `X-Hub-Signature-256` 或 `X-Webhook-Signature` 验证
- 测试模式：发送测试事件到回调URL
- 本地开发：用ngrok/localtunnel暴露本地服务

---

## Phase 7: GraphQL vs REST

### 7.1 核心差异

| 维度 | REST | GraphQL |
|------|------|--------|
| 数据获取 | 固定端点返回固定结构 | 客户端声明需要什么字段 |
| 请求数量 | 多个端点组合 | 单请求获取嵌套数据 |
| 缓存 | 简单（URL级HTTP缓存） | 复杂（需要客户端缓存） |
| 学习曲线 | 低 | 中高 |
| 自动文档 | 难（需额外工具） | 内省（自带） |
| 性能优化 | 简单 | 容易N+1问题 |
| 文件上传 | 原生支持 | 需额外处理 |

### 7.2 REST适用场景

- 简单的CRUD操作
- 公共API（需要HTTP缓存）
- 带宽敏感（移动端）
- 团队不熟悉GraphQL
- 微服务架构（各服务独立）

### 7.3 GraphQL适用场景

- 复杂的数据依赖图（嵌套关联）
- 多个客户端类型（Web/Mobile/IoT）
- 快速迭代的产品（减少API版本）
- 精确数据需求（避免Over-fetching）
- 自带内省查询，工具链成熟

### 7.4 典型N+1问题及解决

**N+1问题：** 一个用户列表，每个用户又请求订单
```graphql
# 一次查询获取100个用户，但触发100次订单查询
query {
  users(first: 100) {
    name
    orders { total }  # N+1!
  }
}
```

**DataLoader解决：**
```python
class OrderLoader(DataLoader):
    def batch_load_fn(self, user_ids):
        orders = db.fetch_orders_by_user_ids(user_ids)
        return [orders.get(uid, []) for uid in user_ids]

# 使用
orders = OrderLoader().load(user_id)  # 批量加载
```

### 7.5 REST与GraphQL共存

很多团队选择共存：
- REST：简单CRUD、公共API、文件上传
- GraphQL：复杂查询、内部产品API

---

## Phase 8: API文档自动生成

### 8.1 文档生成工具链

| 工具 | 类型 | 特点 |
|------|------|------|
| OpenAPI/Swagger | 规范 | 事实标准，生态丰富 |
| Redoc | 文档渲染 | 美观、支持Swagger UI |
| Stoplight | 平台 | 设计+文档+Mock一体化 |
| Postman | 集合管理 | 文档+测试+Mock |
| Scalar | API参考 | 现代、OpenAPI优先 |
| Mintlify | 文档 | 开发者友好、现代UI |

### 8.2 OpenAPI规范（推荐）

```yaml
openapi: 3.1.0
info:
  title: 用户服务API
  version: 2.0.0
  description: 用户管理相关接口

servers:
  - url: https://api.example.com/v2
    description: 生产环境
  - url: https://staging-api.example.com/v2
    description: 预发环境

paths:
  /users:
    get:
      operationId: listUsers
      summary: 获取用户列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
        '401':
          $ref: '#/components/responses/Unauthorized'

components:
  schemas:
    UserList:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/User'
        meta:
          $ref: '#/components/schemas/PaginationMeta'
    User:
      type: object
      required: [id, name, email]
      properties:
        id:
          type: string
          example: "usr_abc123"
        name:
          type: string
          example: "张三"
        email:
          type: string
          format: email
        created_at:
          type: string
          format: date-time
    PaginationMeta:
      type: object
      properties:
        total:
          type: integer
        page:
          type: integer
        page_size:
          type: integer
        has_next:
          type: boolean

  responses:
    Unauthorized:
      description: 未认证
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

### 8.3 文档最佳实践

**代码即文档：**
```python
# OpenAPI注释（FastAPI示例）
@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """
    获取用户详情
    
    - 用户ID为必填路径参数
    - 返回用户的完整信息
    
    ### 响应
    - 200: 用户信息
    - 404: 用户不存在
    """
    return await user_service.get(user_id)
```

**文档维护：**
- 文档与代码同仓库，PR时同步更新
- CI中验证OpenAPI spec合法性
- 自动从Spec生成Mock Server供调用方测试
- 版本化文档（/v1/docs, /v2/docs）

### 8.4 SDK自动生成

| 工具 | 语言 | 特点 |
|------|------|------|
| openapi-generator | 40+种 | 全链路生成 |
| typescript-fetch | TS/JS | 轻量 |
| go-swagger | Go | 成熟 |

```bash
# 生成Python客户端
openapi-generator generate \
  -i openapi.yaml \
  -g python \
  -o ./generated/python

# 生成TypeScript客户端
openapi-generator generate \
  -i openapi.yaml \
  -g typescript-fetch \
  -o ./generated/ts
```

---

## Phase 9: 限流与熔断

### 9.1 限流维度

| 维度 | 说明 | 适用场景 |
|------|------|----------|
| 请求数/时间 | 固定时间窗口内允许的请求数 | 通用限流 |
| 并发数 | 同时处理的请求数 | 保护后端资源 |
| 资源消耗 | CPU/内存/连接池 | 更精细控制 |
| 用户维度 | per-user / per-API-key | 多租户隔离 |

### 9.2 限流算法

**固定窗口计数器：**
```
窗口：1分钟，允许1000请求
窗口内计数，超过则拒绝
问题：边界突刺（0:59和1:01各来1000请求）
```

**滑动窗口日志：**
```
记录每个请求时间戳
统计窗口内请求数
精确但内存消耗大
```

**令牌桶（推荐）：**
```
桶容量：100令牌
补充速度：10令牌/秒
每次请求消耗1令牌
允许突发（积累的令牌）
```

```python
import time
import threading

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # 补充速度（令牌/秒）
        self.capacity = capacity   # 桶容量
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_refill = now
```

**漏桶：**
```
请求以任意速率进入
以固定速率输出到后端
平滑处理突发流量
```

### 9.3 限流响应格式

**HTTP Header：**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705312800
X-RateLimit-Window: 60
```

**429 Too Many Requests：**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "retry_after": 60,
    "limit": 1000,
    "window": "60s"
  }
}
```

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json
```

### 9.4 分布式限流

单机限流无法跨节点生效，需要分布式方案：

**Redis + Lua：**
```lua
-- 令牌桶分布式实现
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local fill_time = capacity / rate
local ttl = math.floor(fill_time) + 1

local tokens = tonumber(redis.call('get', key))
if tokens == nil then
    tokens = capacity
end

local last_time = tonumber(redis.call('get', key .. ':last'))
if last_time == nil then
    last_time = now
end

local delta = math.max(0, now - last_time)
local filled = delta * rate
tokens = math.min(capacity, tokens + filled)

local allowed = 0
if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
end

redis.call('set', key, tokens)
redis.call('set', key .. ':last', now)
redis.call('expire', key, ttl)

return {allowed, tokens}
```

**限流粒度：**
- 全局限流：`/api/*` 整体限制
- 端点限流：`/api/v1/users` vs `/api/v1/orders` 独立限制
- 用户限流：per-api-key独立限制

### 9.5 熔断设计

**熔断器状态：**
```
CLOSED（正常）→ OPEN（熔断）→ HALF_OPEN（探测）
│                    │
←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

| 状态 | 行为 | 触发条件 |
|------|------|----------|
| CLOSED | 正常请求通过，失败计数 | 初始化状态 |
| OPEN | 请求直接失败，快速返回 | 失败率>阈值 |
| HALF_OPEN | 允许部分请求通过 | OPEN后超时 |

**熔断参数：**
```yaml
circuit_breaker:
  failure_threshold: 50%    # 失败率阈值
  success_threshold: 3       # HALF_OPEN→CLOSED需要的成功次数
  timeout: 30s               # OPEN→HALF_OPEN等待时间
  volume_threshold: 10      # 最小请求数（避免小样本误判）
```

**熔断响应：**
```json
{
  "error": {
    "code": "CIRCUIT_BREAKER_OPEN",
    "message": "服务暂时不可用，请稍后重试",
    "retry_after": 30
  }
}
```

### 9.6 限流+熔断配合

```
请求 → 限流检查 → 熔断检查 → 处理请求
         ↓            ↓
      429限流      503熔断
      快速返回     快速返回
```

**实践建议：**
- 限流优先：过滤掉明显超量的请求
- 熔断兜底：防止级联故障
- 分层限流：API Gateway层 + 应用层
- 监控告警：限流触发、熔断开启时告警

---

## Phase 10: 缓存策略

### 10.1 HTTP缓存

**Cache-Control：**
```http
Cache-Control: public, max-age=3600
Cache-Control: private, no-cache
Cache-Control: no-store
```

**ETag + If-None-Match：**
```http
ETag: "v12345"
If-None-Match: "v12345"  # 匹配则返回304
```

### 10.2 缓存层次

| 层次 | TTL | 说明 |
|------|-----|------|
| CDN边缘 | 分钟-小时 | 静态资源、公开数据 |
| API Gateway | 秒-分钟 | 可缓存的GET响应 |
| 客户端 | 自定义 | 移动端、Web本地存储 |

### 10.3 缓存键设计

- 规范化：去掉不必要的query参数
- 版本化：包含数据版本号
- 唯一性：避免不同接口缓存冲突

---

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "API返回格式无所谓，客户端能解析就行" | API是契约，改变返回格式会破坏客户端 | 遵循标准响应格式 |
| "错误信息详细点好，帮用户调试" | 详细错误信息是给开发者看的，不是用户 | 面向用户的消息和面向开发者的日志分开 |
| "用POST就够了，GET不安全" | 正确使用HTTP方法本身就是安全的一部分 | 按语义使用正确的方法 |
| "版本管理太麻烦，上线后再说" | breaking change后再迁移成本更高 | 首个版本就规划版本策略 |
| "REST足够好了，不需要GraphQL" | 视场景而定，复杂关联查询GraphQL更优 | 评估数据获取模式再做选型 |
| "限流影响可用性" | 不限流可能导致服务雪崩 | 分层限流+熔断保障核心功能 |

## Red Flags

- URL中包含动词（/getUser, /doLogin）
- 返回数据结构不一致
- 错误响应没有标准格式
- 没有分页的大型集合API
- 敏感信息在URL或响应中
- 缺少请求ID用于追踪
- 没有限流和熔断
- API没有文档或文档与实现脱节
- Webhook没有签名验证
- 混用REST和GraphQL时没有明确边界

## Verification

验证清单：

- [ ] URL符合RESTful规范
- [ ] 请求响应格式符合标准
- [ ] 错误码体系完整
- [ ] 错误响应有标准格式，包含request_id
- [ ] 分页实现正确（光标分页适合大数据量）
- [ ] 认证授权机制安全
- [ ] 限流已配置，429响应包含Retry-After
- [ ] 熔断机制已实现
- [ ] 版本策略已定义
- [ ] Breaking change有迁移计划和Deprecation机制
- [ ] API文档完整且与实现一致
- [ ] Webhook有签名验证和幂等处理
- [ ] 危险输入有验证和过滤

---

## 参考资料

- [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [REST API Design Rulebook](https://www.oreilly.com/library/view/rest-api-design/9781449317907/)
- [OpenAPI Specification 3.1](https://spec.openapis.org/oas/latest.html)
- [Stripe API Design](https://stripe.com/blog/api-design)
- [Webhook安全实践](https://docs.stripe.com/webhooks/best-practices)
