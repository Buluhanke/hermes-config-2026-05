---
name: deprecation-and-migration
description: 弃用与迁移 — 优雅地移除旧代码，同时保持向后兼容。
triggers:
  - "需要移除某个功能/接口"
  - "需要升级到新版本"
  - "需要迁移到新技术栈"
  - "发现某个依赖有严重安全问题"
  - "需要清理技术债"
---

# Deprecation and Migration

## Overview

删除代码是软件开发中最难的事情之一。弃用不是简单的删除，而是有计划、有沟通、有回滚的完整流程。好的弃用策略让用户有时间迁移，让开发者在受控环境中清理债务。

## When to Use

- 移除旧功能
- 升级依赖版本
- 迁移技术栈
- 修复有安全问题的依赖
- 清理长期积累的技术债

## Process

### Phase 1: 评估影响

#### 1.1 识别使用方
- 内部调用者：哪些模块在用？
- 外部调用者：哪些用户在用？
- API调用者：有哪些客户端？

#### 1.2 评估迁移成本
- 迁移需要多少工作量？
- 用户需要多少时间迁移？
- 有没有替代方案？

#### 1.3 制定时间线
```
废弃预告 → 废弃期 → 移除
   ↓         ↓        ↓
  v1.x      v2.0     v3.0
```

### Phase 2: 废弃宣告

#### 2.1 废弃警告
- 在代码中添加deprecation警告
- 在文档中明确标注废弃内容
- 在CHANGELOG中说明

#### 2.2 废弃信息格式
```python
import warnings

def old_function():
    warnings.warn(
        "old_function将在v2.0中移除，请使用new_function",
        DeprecationWarning,
        stacklevel=2
    )
    # ... 旧实现
```

#### 2.3 沟通计划
- 发布废弃公告
- 提供迁移指南
- 设置迁移答疑渠道

### Phase 3: 迁移支持

#### 3.1 提供替代方案
- 新功能是什么？
- 如何迁移？
- 有没有迁移工具？

#### 3.2 兼容性层
- 如果可能，提供兼容层
- 兼容层应该转发到新实现
- 兼容层也标记为废弃

#### 3.3 测试迁移
- 确保迁移路径有测试
- 提供迁移测试套件
- 记录常见迁移问题

### Phase 4: 执行移除

#### 4.1 移除前的检查
- 所有已知的调用者是否已迁移？
- 废弃警告是否已达到足够时间？
- 是否有回滚计划？

#### 4.2 执行移除
- 移除废弃代码
- 更新文档
- 确认测试通过

#### 4.3 移除后
- 通知用户已移除
- 监控是否有遗漏的调用
- 清理相关的配置和脚本

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "直接删除更快，用户会理解的" | 直接删除会破坏用户代码 | 遵循废弃流程 |
| "废弃警告太烦人，去掉" | 废弃警告是用户迁移的唯一信号 | 保留直到完全移除 |
| "用户应该自己看文档" | 用户不一定知道要迁移 | 主动通知用户 |
| "兼容层太麻烦，不做了" | 兼容层让迁移更平滑 | 尽量提供兼容层 |

## Red Flags

- 没有通知就移除功能
- 废弃和移除之间没有足够时间
- 没有提供替代方案
- 废弃警告不包含迁移指南
- 移除后才发现还有人在用
- 兼容层和旧实现行为不一致

## Verification

验证清单：

- [ ] 使用方已识别
- [ ] 迁移时间线已制定
- [ ] 废弃警告已添加
- [ ] 迁移指南已提供
- [ ] 兼容层已提供（如果可能）
- [ ] 用户已通知
- [ ] 移除前确认所有调用者已迁移
- [ ] 移除后确认无遗漏

---

# API版本迁移指南

## 何时需要API版本迁移

- 现有API契约需要变更（请求/响应结构）
- 需要删除或重命名字段
- 认证机制变更
- 性能优化需要破坏性变更

## 版本策略

### 路径版本（最常见）
```
/api/v1/users  →  /api/v2/users
```

### Header版本
```
Accept: application/vnd.api+json; version=2
```

### 演化版本（Evolutionary APIs）
不主动破坏，通过添加而非删除来演进：
- 新增字段（可选）
- 新增端点
- 扩展枚举值

## 迁移流程

### Phase 1: 双版本运行
```
v1  →  内部实现A
v2  →  内部实现B
     ↓
   共享引擎
```

### Phase 2: 强制迁移
- v1 设置 `Sunset` header
- v1 响应中包含 `Deprecation: true` 和 `Migration_guide: /docs/v1-to-v2`

### Phase 3: 废弃v1
```http
HTTP/1.1 410 Gone
Content-Type: application/problem+json
{
  "type": "https://api.example.com/errors/version-unsupported",
  "title": "API Version Retired",
  "detail": "v1已废弃，请迁移到v2",
  "migration_guide": "/docs/v1-to-v2"
}
```

## 字段迁移策略

### 添加字段
```json
// v1响应
{ "name": "张三" }

// v2响应（新增字段）
{ "name": "张三", "display_name": "张三" }
```

### 重命名字段
```json
// v1响应
{ "user_name": "张三" }

// v2响应（别名兼容）
{ "display_name": "张三" }

// v2也保留旧字段（临时兼容）
{ "display_name": "张三", "user_name": "张三" }
```

### 删除字段
```json
// v2开始标记废弃
{ "display_name": "张三", "user_name": "*** DEPRECATED ***" }

// 最终移除
{ "display_name": "张三" }
```

## 认证迁移

### API Key → OAuth2
```
阶段1: 接受旧API Key（生成兼容token）
阶段2: 旧API Key必须换取新token
阶段3: 拒绝旧API Key
```

### Token刷新
```python
# 迁移时保留新旧两种token验证
def validate_token(token: str) -> User:
    # 尝试新JWT格式
    try:
        return validate_jwt(token)
    except InvalidJWT:
        # 降级到旧格式（记录日志）
        legacy_user = validate_legacy_token(token)
        logger.warning(f"Legacy token used by {legacy_user.id}")
        return legacy_user
```

## 向后兼容检查清单

- [ ] 新字段是可选的吗？
- [ ] 旧字段还在响应中吗？（至少有过渡期）
- [ ] 字段类型改变了吗？（字符串→数字需特别注意）
- [ ] 枚举值增加了吗？（客户端switch会漏掉新值）
- [ ] 必填字段变可选了吗？
- [ ] 错误码改变了吗？

---

# 1688 API升级路径

## 1688 API版本现状

1688开放平台主要API版本为 **v1**（原型），
新API基于 **阿里云OpenAPI** 体系，认证走 **阿里云AK/SK**。

## 常见API升级场景

### 商品API从旧版迁移到新版

```python
# 旧版（1688早期API）
import requests

def get_product_old(product_id):
    resp = requests.get(
        "https://gw.open.1688.com/openapi/param2/1/com.alibaba.product/...",
        params={"productID": product_id}
    )
    return resp.json()

# 新版（阿里云OpenAPI）
from aliyunsdkcore.client import AcsClient
from aliyunsdkproduct.request.v20180505 import GetProductRequest

def get_product_new(product_id):
    client = AcsClient(ak, sk, "cn-hangzhou")
    request = GetProductRequest()
    request.set_ProductId(product_id)
    return client.do_action(request)
```

### 订单API迁移

```python
# 旧版路径
"https://gw.open.1688.com/openapi/param2/1/com.alibaba.trade/..."

# 新版路径（阿里云产品云市场）
"https://market.aliyun.com/..."
# 或
"https://open.1688.com/openapi/..."
```

## 认证升级

### 旧版：AppKey + AppSecret
```python
# 旧签名算法
def sign_old(params, app_secret):
    sorted_params = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_params)
    return md5(sign_str + app_secret).hexdigest()
```

### 新版：阿里云AK/SK
```python
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.auth.credential import AccessKeyCredential

credential = AccessKeyCredential(access_key_id, access_key_secret)
client = AcsClient(credential, "cn-hangzhou")
```

## 迁移检查清单

- [ ] 已注册阿里云账号并获取AK/SK
- [ ] 已申请需要API产品的访问权限
- [ ] 旧版API调用已记录（用于回归测试）
- [ ] 新版API签名验签已测试
- [ ] 限流/配额已确认
- [ ] 错误码已对照（新旧错误码映射表）

## 限流与配额

| API类型 | 默认QPS | 备注 |
|--------|---------|------|
| 商品查询 | 10 | 可申请提高 |
| 订单创建 | 2 | 需单独权限 |
| 批量操作 | 1 | 批大小有限制 |

```python
# 推荐：请求间隔控制
import time
def rate_limited_call(func, *args, **kwargs):
    while True:
        result = func(*args, **kwargs)
        if "Code" in result and "TooManyRequests" in result["Code"]:
            time.sleep(1)  # 指数退避更好
            continue
        return result
```

---

# 模型切换迁移

## 何时需要模型迁移

- LLM模型版本升级（GPT-3.5 → GPT-4）
- 切换到不同的LLM提供商
- 本地模型替代云端模型
- 蒸馏模型替代大模型
- 微调后模型替代基础模型

## 迁移维度评估

| 维度 | 检查项 |
|-----|--------|
| 输入兼容 | Prompt格式是否相同？Token限制？ |
| 输出兼容 | Response格式是否相同？工具调用兼容？ |
| 能力差异 | 推理能力差异？幻觉率差异？ |
| 成本 | Token价格？延迟？ |
| 合规 | 数据是否外传？ |

## Prompt兼容性

### 结构化输出迁移
```python
# OpenAI GPT-4
def chat_openai(prompt, schema):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object", "schema": schema}
    )
    return json.loads(response.choices[0].message.content)

# Anthropic Claude
def chat_claude(prompt, schema):
    response = claude.messages.create(
        model="claude-3-opus",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object", "schema": schema}
    )
    return json.loads(response.content[0].text)
```

### 通用Prompt适配层
```python
class LLMAdapter:
    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
    
    def chat(self, prompt: str, **kwargs) -> str:
        if self.provider == "openai":
            return self._chat_openai(prompt, **kwargs)
        elif self.provider == "anthropic":
            return self._chat_anthropic(prompt, **kwargs)
        elif self.provider == "ollama":
            return self._chat_ollama(prompt, **kwargs)
        raise NotImplementedError(f"Provider {self.provider} not supported")
    
    def _chat_openai(self, prompt, **kwargs):
        # OpenAI实现
        ...
    
    def _chat_anthropic(self, prompt, **kwargs):
        # Anthropic实现
        ...
    
    def _chat_ollama(self, prompt, **kwargs):
        # 本地Ollama实现
        ...
```

## 工具调用（Function Calling）迁移

```python
# OpenAI Function Calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}}
            }
        }
    }
]

# Anthropic Tool Use（概念对应）
tools = [
    {
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}}
        }
    }
]

# 统一抽象
class ToolCallAdapter:
    @staticmethod
    def to_openai(tools: list) -> list:
        return [{"type": "function", "function": t} for t in tools]
    
    @staticmethod
    def to_anthropic(tools: list) -> list:
        return [{"name": t["function"]["name"], 
                 "description": t.get("description", ""),
                 "input_schema": t["function"]["parameters"]} 
                for t in tools]
```

## 模型切换时的回归测试

```python
# golden_set.jsonl
{"input": "北京今天天气如何？", "expected_tools": ["get_weather"], "expected_key": "北京"}
{"input": "帮我查下上海的温度", "expected_tools": ["get_weather"], "expected_key": "上海"}

# 对比测试
def regression_test(new_model: str, golden_set: list) -> TestReport:
    adapter = LLMAdapter(provider="openai", model=new_model)
    results = []
    for case in golden_set:
        output = adapter.chat(case["input"])
        # 对比output与expected
        results.append(compare(case, output))
    return summarize(results)
```

## 降级策略

```python
class ModelFailover:
    def __init__(self):
        self.models = [
            ("openai", "gpt-4o"),      # 主
            ("anthropic", "claude-3-opus"),  # 备1
            ("openai", "gpt-3.5-turbo"),     # 备2（兜底）
        ]
    
    def chat(self, prompt: str) -> str:
        last_error = None
        for provider, model in self.models:
            try:
                adapter = LLMAdapter(provider, model)
                return adapter.chat(prompt)
            except Exception as e:
                last_error = e
                logger.warning(f"{provider}/{model} failed: {e}")
                continue
        raise last_error  # 全部失败
```

---

# 数据库Schema迁移

## 迁移原则

1. **永远不要直接修改生产数据库**
2. **每次只做一个方向的迁移**
3. **确保回滚路径存在**
4. **新旧代码可以同时运行**

## 迁移策略对比

| 策略 | 适用场景 | 风险 |
|-----|---------|------|
| 扩展-收缩（Expand-Contract） | 重命名列、删除表 | 迁移周期长 |
| 影子表（Shadow Table） | 大表结构变更 | 需要双写 |
| 在线DDL | MySQL/PG原生支持 | 性能开销 |
| 蓝绿部署 | 有主从切换能力 | 资源翻倍 |

## 扩展-收缩（Expand-Contract）

### Step 1: 扩展（Expand）
```sql
-- 添加新列（允许NULL或默认值）
ALTER TABLE users ADD COLUMN display_name VARCHAR(100) DEFAULT '';

-- 添加新表
CREATE TABLE users_v2 (
    id BIGSERIAL PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建同步视图（可选）
CREATE VIEW users_current AS
SELECT id, display_name, email, created_at FROM users_v2;
```

### Step 2: 数据迁移
```python
# 分批迁移，避免锁表
BATCH_SIZE = 1000

def migrate_users():
    offset = 0
    while True:
        rows = db.fetch(
            "SELECT id, user_name FROM users WHERE id > %s ORDER BY id LIMIT %s",
            (offset, BATCH_SIZE)
        )
        if not rows:
            break
        
        for row in rows:
            db.execute(
                "UPDATE users_v2 SET display_name = %s WHERE id = %s",
                (row["user_name"], row["id"])
            )
        offset = rows[-1]["id"]
        time.sleep(0.1)  # 限速
```

### Step 3: 收缩（Contract）
```sql
-- 确认迁移完成，删除旧列/表
ALTER TABLE users DROP COLUMN user_name;

DROP TABLE users_old;
```

## 影子表迁移

```python
# 双写：同时写入新旧表
def create_user_v2(user_data: dict) -> User:
    # 写入新表
    new_user = db.insert("users_v2", {
        "display_name": user_data["name"],
        "email": user_data["email"]
    })
    
    # 写入旧表（保持兼容）
    db.execute(
        "INSERT INTO users (id, user_name, email) VALUES (%s, %s, %s)",
        (new_user.id, user_data["name"], user_data["email"])
    )
    
    return new_user

# 读取：只从新表读
def get_user_v2(user_id: int) -> User:
    return db.fetch_one("SELECT * FROM users_v2 WHERE id = %s", (user_id,))
```

## 在线DDL（MySQL）

```sql
-- 使用 pt-online-schema-change（Percona Toolkit）
pt-online-schema-change \
    --alter "ADD COLUMN display_name VARCHAR(100)" \
    --execute \
    D=touchgraph, t=users

-- 原生在线DDL（MySQL 5.6+）
ALTER TABLE users ADD COLUMN display_name VARCHAR(100), 
    ALGORITHM=INPLACE, LOCK=NONE;
```

## 回滚计划

```sql
-- 回滚脚本模板
-- rollback_001_add_display_name.sql

-- 1. 从新表读数据写回旧表
INSERT INTO users (id, user_name, email)
SELECT id, display_name, email FROM users_v2
ON CONFLICT (id) DO UPDATE SET
    user_name = EXCLUDED.user_name;

-- 2. 删除新表
DROP TABLE users_v2;

-- 3. 删除新列
ALTER TABLE users DROP COLUMN display_name;
```

## Schema迁移检查清单

- [ ] 变更已评审（DBA + 业务）
- [ ] 备份已确认
- [ ] 迁移窗口已沟通
- [ ] 回滚脚本已准备
- [ ] 迁移脚本已测试（staging）
- [ ] 监控告警已设置
- [ ] 迁移后数据校验SQL已准备

## 数据校验

```sql
-- 迁移后校验
SELECT 
    COUNT(*) as total,
    COUNT(display_name) as filled,
    COUNT(*) - COUNT(display_name) as null_count
FROM users;

-- 新旧表一致性校验
SELECT COUNT(*) 
FROM users_v2 t2
LEFT JOIN users t1 ON t2.id = t1.id
WHERE t1.id IS NULL;
```
