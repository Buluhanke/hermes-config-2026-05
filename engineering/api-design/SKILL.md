---
name: api-design
description: API设计规范 — RESTful设计、错误处理、分页、版本管理、安全性。
triggers:
  - "设计新的API接口"
  - "重构现有API"
  - "APIbreaking change"
  - "需要统一API风格"
  - "API文档不规范"
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

## Process

### Phase 1: API设计原则

#### 1.1 RESTful基础
- 使用标准HTTP方法（GET/POST/PUT/PATCH/DELETE）
- 资源命名用名词（/users, /orders）
- 嵌套资源有限度（/users/123/orders 合理，/users/123/orders/456/items 过度）
- 使用HTTP状态码（200/201/400/401/403/404/500）

#### 1.2 URL设计
```
✓ GET /users              用户列表
✓ GET /users/123          用户详情
✓ POST /users             创建用户
✓ PUT /users/123          更新用户
✓ DELETE /users/123       删除用户
✓ GET /users/123/orders   用户订单

✗ GET /getUsers
✗ POST /createUser
✗ /api/get_data.php
```

#### 1.3 命名规范
- 小写+下划线或中划线（/user-orders 或 /user_orders）
- 保持简洁，但不过度简化
- 使用复数名词表示集合
- 使用具体名称，不要泛型

### Phase 2: 请求与响应

#### 2.1 请求格式
- JSON作为标准数据格式
- Content-Type: application/json
- 日期格式：ISO 8601（2024-01-15T10:30:00Z）
- 金额：使用最小单位（分而非元）或明确标注单位
- 分页参数：page/page_size 或 cursor

#### 2.2 响应格式
```json
{
  "data": { },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  },
  "error": null
}
```

错误响应：
```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "用户不存在",
    "details": {}
  }
}
```

#### 2.3 分页设计
- 偏移分页：`?page=1&page_size=20`
- 光标分页：`?cursor=abc123`（大数据量推荐）
- 返回元数据：`total_count`, `has_next`

### Phase 3: 错误处理

#### 3.1 错误码体系
```
4xx 客户端错误
400 Bad Request         请求格式错误
401 Unauthorized        未认证
403 Forbidden           无权限
404 Not Found           资源不存在
409 Conflict            冲突（如重复创建）
422 Unprocessable       业务逻辑错误
429 Too Many Requests   请求过于频繁

5xx 服务端错误
500 Internal Server     服务器内部错误
502 Bad Gateway         上游服务错误
503 Service Unavailable 服务不可用
504 Gateway Timeout     超时
```

#### 3.2 错误响应规范
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求验证失败",
    "request_id": "req_abc123",
    "details": [
      {"field": "email", "message": "邮箱格式不正确"}
    ]
  }
}
```

#### 3.3 不要暴露内部细节
- 错误信息不要包含堆栈
- 错误ID用于日志关联，不用于客户端判断
- 通用错误消息用于展示，具体错误记录日志

### Phase 4: 安全与性能

#### 4.1 认证授权
- 使用标准认证（Bearer Token / OAuth2）
- 不要在URL中传递token
- 敏感操作需要额外验证

#### 4.2 速率限制
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705312800
```

超过限制返回：
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁",
    "retry_after": 60
  }
}
```

#### 4.3 缓存控制
- GET资源使用ETag/Last-Modified
- 允许客户端条件请求
- 明确Cache-Control策略

### Phase 5: 版本管理

#### 5.1 版本策略
- URL路径：`/api/v1/users`
- Header：`Accept: application/vnd.api+json; version=1`
- 不建议：只有major版本，没有minor/patch区分

#### 5.2 Breaking Change
- 不删除字段（标记deprecated）
- 不改变字段类型
- 不改变语义
- 不改变必需性
- 新增可选字段可以

#### 5.3 Deprecation
```json
{
  "data": {
    "id": "123",
    "name": "张三",
    "old_field": "已废弃，请使用 new_field",
    "new_field": "新字段值"
  },
  "warnings": [
    {
      "code": "DEPRECATED_FIELD",
      "field": "old_field",
      "message": "此字段将在v3中移除"
    }
  ]
}
```

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "API返回格式无所谓，客户端能解析就行" | API是契约，改变返回格式会破坏客户端 | 遵循标准响应格式 |
| "错误信息详细点好，帮用户调试" | 详细错误信息是给开发者看的，不是用户 | 面向用户的消息和面向开发者的日志分开 |
| "用POST就够了，GET不安全" | 正确使用HTTP方法本身就是安全的一部分 | 按语义使用正确的方法 |
| "版本管理太麻烦，上线后再说" | breaking change后再迁移成本更高 | 首个版本就规划版本策略 |

## Red Flags

- URL中包含动词（/getUser, /doLogin）
- 返回数据结构不一致
- 错误响应没有标准格式
- 没有分页的大型集合API
- 敏感信息在URL或响应中
- 缺少请求ID用于追踪
- 没有速率限制
- API没有文档

## Verification

验证清单：

- [ ] URL符合RESTful规范
- [ ] 请求响应格式符合标准
- [ ] 错误码使用正确
- [ ] 错误响应有标准格式
- [ ] 分页实现正确
- [ ] 认证授权机制安全
- [ ] 速率限制已配置
- [ ] 版本策略已定义
- [ ] Breaking change有迁移计划
- [ ] API文档完整且与实现一致
