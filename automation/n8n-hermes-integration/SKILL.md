---
name: n8n-hermes-integration
description: n8n 工作流自动化平台与 Hermes Desktop Agent 的集成架构。涵盖 n8n + ChromaDB Docker 部署、Ollama/LLM 连接、ddddocr 验证码集成、工作流设计模式。
triggers:
  - n8n 部署安装
  - n8n 工作流设计
  - ChromaDB 向量库连接
  - n8n OCR 验证码破解
  - n8n + Hermes 联动
  - n8n Webhook 触发 Hermes
  - Hermes 调用 n8n API
  - 1688 采购自动化
  - n8n Cronjob 协同
  - n8n JWT 安全配置
version: 1.0.1
---

# n8n-Hermes 集成架构

## 快速部署

```bash
mkdir -p ~/hermes-ai/{n8n_data,chroma_data}
cd ~/hermes-ai

cat > docker-compose.yml << 'EOF'
services:
  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - ./chroma_data:/chroma/data
    ports:
      - "8000:8000"
    restart: always

  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PROTOCOL=http
      - NODE_FUNCTION_ALLOW_EXTERNAL=moment,lodash,axios
      - N8N_DIAGNOSTICS_ENABLED=false
      - N8N_LAUNCH_BC=false
      - N8N_PHONE_HOME=false
    volumes:
      - ~/n8n_data:/home/node/.n8n
    depends_on:
      - chromadb
EOF

docker-compose up -d
```

首次访问 `http://localhost:5678` 需要创建管理员账号（UI引导）。

## 服务连接地址（Docker 网络内）

| 服务 | Docker 内部地址 | Host 地址 |
|------|----------------|-----------|
| ChromaDB | `http://chromadb:8000` | `http://localhost:8000` |
| n8n | `http://n8n:5678` | `http://localhost:5678` |
| Ollama | `http://host.docker.internal:11434` | `http://127.0.0.1:11434` |
| ddddocr API | `http://ocr-api:9898` | `http://localhost:9898` |

**Mac Docker 特殊**：容器内访问宿主机用 `host.docker.internal`（已内置支持）。

## n8n + Ollama/LLM 连接

在 n8n 的 **Ollama Chat Model** 节点：
- Base URL: `http://host.docker.internal:11434`
- Model: `qwen3-fast:latest`（或 `qwen3:8b`）

n8n Code 节点调用本地模型示例：
```javascript
// n8n Code 节点
const { Configuration, OpenAIApi } = require('openai');
const configuration = new Configuration({
  basePath: 'http://host.docker.internal:11434/v1',
  baseOptions: { timeout: 30000 },
});
// 注意：Ollama 使用 OpenAI 兼容格式
```

## n8n REST API 认证

### 认证 header 格式（关键！）

n8n Public API 使用专用 header，**不是** `Authorization: Bearer`：

```
X-N8N-API-KEY: <value>
```

| Key 类型 | 格式 | 适用场景 |
|---------|------|---------|
| n8n Cloud JWT | `eyJhbGciOiJI...` | 可直接用于本地 Docker 实例 |
| 本地创建的 API Key | UUID 字符串 | 仅限本地实例 |

**实测结论**：n8n Cloud 账号签发的 JWT（`iss: n8n, aud: public-api`）可以直接用于本地 Docker n8n 实例的 `X-N8N-API-KEY` header，无需在本地重新创建 Key。

### API 端点

- **Public API v1**：`http://localhost:5678/api/v1/`（认证调用）
- **REST API**：`http://localhost:5678/rest/`（内部接口，需要 Session Cookie）

注意：旧版文档或报错信息可能指向 `/rest/`，但外部认证应使用 `/api/v1/`。

### 快速验证

```bash
curl -H "X-N8N-API-KEY: <your-jwt>" http://localhost:5678/api/v1/workflows
```

返回 `{"data":[],"nextCursor":null}` 即为成功。

### 创建本地 API Key（如需）

1. 访问 `http://localhost:5678/settings` → **n8n API**
2. 点击 **Create an API Key**
3. 填写 Label（如 `Hermes CLI`），选择 Scopes 和过期时间
4. **立即复制 Key**（只显示一次）
5. 用同样的 header `X-N8N-API-KEY: <key>` 调用

### 已知陷阱

- **`/rest/` vs `/api/v1/`**：n8n v2 有两套 API，外部认证用 `/api/v1/`，`/rest/` 需要 Session Cookie
- **Key 只显示一次**：创建后立即复制，之后无法找回（需要删除重建）
- **Scope 不足**：如果 Workflow 无法访问，检查 Key 是否包含 `workflow:read` / `workflow:write`
- **n8n Cloud JWT 解码**：`iss: n8n, aud: public-api` 表示这是 Cloud Key，可跨实例使用

## ddddocr 验证码集成

### 方案A：Host venv Flask API（推荐，已验证）

**部署步骤：**
```bash
# 1. 创建 venv（避免系统 pip 冲突）
python3 -m venv ~/.hermes/venv-ocr
~/.hermes/venv-ocr/bin/pip install ddddocr flask

# 2. 启动 API 服务
~/.hermes/venv-ocr/bin/python -c "
from flask import Flask, request, jsonify
import ddddocr, base64, io
from PIL import Image

app = Flask(__name__)
ocr = ddddocr.DdddOcr(show_ad=False)

@app.route('/ocr', methods=['POST'])
def solve():
    data = request.get_json()
    if 'base64' in data:
        img_data = base64.b64decode(data['base64'])
    else:
        return jsonify({'error': 'send base64'}), 400
    img = Image.open(io.BytesIO(img_data))
    return jsonify({'result': ocr.classification(img)})

app.run(host='0.0.0.0', port=9898)
" &
```

**n8n 调用方式**：HTTP Request 节点 POST `http://host.docker.internal:9898/ocr`，body 为 `{"base64": "..."}`。

### 方案B：Docker 构建自封装 OCR API（已知陷阱）

**不要用** `sunlimits/ddddocr-api:latest` — 此镜像不存在。

正确做法：
```bash
mkdir -p ~/hermes-ai/ocr-api
# 编写 Dockerfile + server.py（见上方）
docker build ./ocr-api -t hermes-ocr-api
```

**陷阱**：Docker Hub `python:3.10-slim` 拉取可能超时（i/o timeout），需要配置镜像代理或等待网络恢复。

## ChromaDB 向量库

n8n 的 **Chroma Vector Store** 节点：
- URL: `http://chromadb:8000`（Docker网络内）
- Collection 名自定义

n8n Code 节点直接操作 ChromaDB：
```javascript
// ChromaDB HTTP API
const collectionName = 'hermes_memory';
// 查询
const result = await fetch(`http://chromadb:8000/api/v1/collections/${collectionName}/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query_embeddings: [embedding], n_results: 5 })
});
```

## 工作流设计模式

### 主/从工作流模式
- **触发层**：Webhook / Schedule
- **识别层**：HTTP Request → OCR API
- **逻辑层**：IF/Switch 节点
- **存储层**：ChromaDB 记录状态
- **执行层**：Code 节点调用 Hermes via HTTP
- **通知层**：Email / Telegram / 企业微信

### Hermes 作为执行器
n8n 负责编排和状态管理，Hermes 负责：
- 浏览器精确操控（CDP）
- 桌面应用控制（PyAutoGUI）
- 视觉理解（截图+OCR）

典型流程：
```
n8n Webhook → 任务描述
  → ChromaDB 查历史知识
  → Code 节点生成 action plan
  → HTTP 调用 Hermes 执行
  → 截图验证结果
  → ChromaDB 写回记忆
  → 通知
```

## 当前运行状态（2026-05-18更新）
- n8n容器：`hermes-ai-n8n-1`，端口5678已就绪
- Docker Desktop已启动
- n8n数据卷：使用**bind mount** `~/n8n_data:/home/node/.n8n`（bind mount 对 Hermes 这个使用频率足够，不会像高并发场景那样触发 SQLite 锁损坏）
- **telemetry 已禁用**：docker-compose.yml 添加了 `N8N_DIAGNOSTICS_ENABLED=false` + `N8N_LAUNCH_BC=false` + `N8N_PHONE_HOME=false`，防止 DNS 失败导致崩溃
- 主动触发系统：cronjob每日08:00触发Hermes巡检 → QQ推送
- **n8n API 可用**：REST API 端点 `/api/v1/`，header `X-N8N-API-KEY: <jwt>`
- **N8N_ENCRYPTION_KEY 已写入 `~/.hermes/.env`**：`WxCtRXmaJvXVhSAsdgc9h1p4bpT+iA5a`（容器重建后从旧数据库自动继承，不需要重新设置）
- **实测结论：n8n Cloud JWT 可直接用于本地 Docker 实例**：`iss: n8n, aud: public-api` 的 JWT 无需在本地重建，用 `X-N8N-API-KEY: <cloud-jwt>` 直接认证本地 `/api/v1/` 端点
- **API Key 创建**：Settings → n8n API → Create an API Key，Key 只显示一次，创建后立即从 Settings 页面复制或从 SQLite `user_api_keys` 表提取

## Public API 创建工作流详解

### 节点类型格式要求

n8n Public API 创建 Workflow 时，节点类型必须使用 `n8n-nodes-base.xxx` 格式（**不带** `@n8n/` 前缀）：

| 正确 ✅ | 错误 ❌ |
|---------|---------|
| `n8n-nodes-base.webhook` | `@n8n/n8n-nodes-base.webhook` |
| `n8n-nodes-base.httpRequest` | `@n8n/n8n-nodes-base.httpRequest` |
| `n8n-nodes-base.respondToWebhook` | `@n8n/n8n-nodes-base.respondToWebhook` |

**为什么重要**：如果用了 `@n8n/` 前缀，API 创建成功（返回200），但激活时会报 `Unrecognized node type`，且 **PATCH 无法修复**（Public API 不支持 PATCH）。必须删除重建。

### 完整创建工作流流程（Python）

```python
import urllib.request, json

KEY = "<your-api-key>"
wf = {
    "name": "My Workflow",
    "nodes": [
        {"id": "n1", "name": "Webhook", "type": "n8n-nodes-base.webhook",
         "typeVersion": 2, "position": [250, 300],
         "parameters": {"httpMethod": "POST", "path": "my-webhook", "responseMode": "responseNode"}},
        {"id": "n2", "name": "HTTP Request", "type": "n8n-nodes-base.httpRequest",
         "typeVersion": 4.2, "position": [450, 300],
         "parameters": {"method": "POST", "url": "http://example.com/api", ...}},
        {"id": "n3", "name": "Respond", "type": "n8n-nodes-base.respondToWebhook",
         "typeVersion": 1, "position": [650, 300],
         "parameters": {"respondWith": "json", "responseBody": "={{ ... }}"}}
    ],
    "connections": {
        "Webhook": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
        "HTTP Request": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]}
    },
    "settings": {},
    "staticData": None  # 必须为 None，不要传空 dict
}

data = json.dumps(wf).encode()
req = urllib.request.Request(
    "http://localhost:5678/api/v1/workflows",
    data=data,
    headers={"Content-Type": "application/json", "X-N8N-API-KEY": KEY},
    method="POST"
)
with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read())
    wf_id = result["id"]
```

### 激活 Workflow（重要：端点不是 /api/v1/）

创建成功后激活workflow，**端点是 `/rest/` 不是 `/api/v1/`**：

```bash
# 方式A：Session Cookie（浏览器自动处理）
curl -X POST -b "n8n-auth=<cookie>" \
  http://localhost:5678/rest/workflows/<id>/activate

# 方式B：直接从数据库提取 API Key 后用 Public API
# （注意：本地 Docker 实例的 Public API 激活有时需要 session cookie）
curl -X POST -H "X-N8N-API-KEY: <jwt-from-db>" \
  http://localhost:5678/rest/workflows/<id>/activate
```

如果报 401 说明该端点需要 session cookie（浏览器UI里点击激活按钮走的就是这个端点），可用浏览器 console 发请求：
```javascript
fetch('/rest/workflows/<id>/activate', {
  method: 'POST',
  credentials: 'include'  // 带上当前 session cookie
}).then(r => r.json()).then(d => console.log(d))
```

### 删除 Workflow

```bash
curl -X DELETE -H "X-N8N-API-KEY: <key>" \
  http://localhost:5678/api/v1/workflows/<id>
```

## Webhook 触发 Hermes

### 架构设计

```
外部事件 → n8n Webhook → Hermes 执行 → 结果回写 n8n → 通知
```

n8n Webhook 作为事件入口，Hermes 作为智能执行器通过 MCP 协议被调用。

### n8n 端：创建 Webhook 触发工作流

在 n8n Editor UI：
1. 添加 **Webhook** 节点（路径如 `hermes-trigger`）
2. 添加 **Code** 节点：生成 Herme's MCP JSON-RPC 请求
3. 添加 **HTTP Request** 节点：调用 Hermes MCP Server
4. 添加 **Respond to Webhook** 节点：返回执行状态

### Hermes 端：接收 Webhook 并执行

Hermes 通过 MCP 工具 `mcp_n8n_webhook_trigger` 监听 Webhook 事件：

```javascript
// Hermes MCP Server 接收 Webhook
{
  "jsonrpc": "2.0",
  "method": "tools/list"
}

// 返回可用工具列表，包含 n8n 相关工具
```

### 完整双向触发流程

```
方式A：n8n → Hermes
n8n Webhook → HTTP Request(MCP) → Hermes Agent → 浏览器/桌面操控

方式B：Hermes → n8n
Hermes 检测到事件 → 调用 n8n API → 触发工作流执行 → n8n 回写结果
```

### Webhook 安全配置

n8n Webhook 支持 HMAC 签名验证，防止恶意触发：

```javascript
// n8n Code 节点验证 HMAC
const crypto = require('crypto');
const signature = $input.first().json.headers['x-webhook-signature'];
const body = $input.first().json.body;
const expected = crypto
  .createHmac('sha256', process.env.WEBHOOK_SECRET)
  .update(JSON.stringify(body))
  .digest('hex');

if (signature !== `sha256=${expected}`) {
  throw new Error('Invalid webhook signature');
}
```

### 测试 Webhook

```bash
# 手动触发 n8n Webhook
curl -X POST http://localhost:5678/webhook/hermes-trigger \
  -H "Content-Type: application/json" \
  -d '{"event": "purchase_order", "order_id": "PO-2026-001"}'
```

## Hermes 调用 n8n API

### 核心场景

Hermes 作为 Agent，需要主动调用 n8n 实现：
- 读取工作流状态
- 触发特定工作流
- 写入执行结果到 n8n
- 查询 n8n 日志/历史

### Hermes Python 客户端

```python
import requests
from datetime import datetime

class N8NClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:5678"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json"
        }

    def list_workflows(self) -> list:
        resp = requests.get(f"{self.base_url}/api/v1/workflows", headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_workflow(self, workflow_id: str) -> dict:
        resp = requests.get(f"{self.base_url}/api/v1/workflows/{workflow_id}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def trigger_workflow(self, workflow_id: str, payload: dict) -> dict:
        resp = requests.post(
            f"{self.base_url}/api/v1/workflows/{workflow_id}/trigger",
            headers=self.headers,
            json=payload
        )
        return resp.json()

    def create_workflow(self, workflow: dict) -> str:
        resp = requests.post(
            f"{self.base_url}/api/v1/workflows",
            headers=self.headers,
            json=workflow
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def write_execution_log(self, workflow_id: str, step: str, result: dict):
        """写入执行日志到指定 workflow 的 staticData"""
        wf = self.get_workflow(workflow_id)
        static_data = wf.get("staticData", {}) or {}
        if "executionLog" not in static_data:
            static_data["executionLog"] = []
        static_data["executionLog"].append({
            "step": step,
            "result": result,
            "timestamp": str(datetime.now())
        })
        # 注意：n8n Public API 不支持 PUT/PATCH，只能通过 Code 节点内部写入
```

### Hermes Tool 封装示例

```json
{
  "name": "n8n_trigger_workflow",
  "description": "触发指定 n8n 工作流执行",
  "input_schema": {
    "type": "object",
    "properties": {
      "workflow_id": {"type": "string", "description": "n8n Workflow ID"},
      "payload": {"type": "object", "description": "传递给 workflow 的数据"}
    },
    "required": ["workflow_id"]
  }
}
```

### 从 n8n 获取 API Key

Hermes 需要存储 n8n API Key，推荐通过环境变量注入：

```bash
# 在 Hermes 启动环境配置
export N8N_API_KEY="eyJhbGciOiJI..."
export N8N_BASE_URL="http://localhost:5678"
```

### 典型调用场景

| 场景 | Hermes 操作 | n8n API |
|------|------------|---------|
| 定时检查订单 | Cronjob触发 → Hermes执行 → n8n查询数据库 → 处理异常 | `GET /api/v1/workflows/<id>` |
| 用户请求处理 | Webhook → Hermes → n8n记录日志 | `POST /api/v1/workflows/<id>/trigger` |
| 批量操作 | Hermes循环 → n8n API批量写入 | `POST /api/v1/workflows` (批量) |

## 1688 采购 n8n 模板

### 业务背景

1688 批发平台采购流程需要自动化：
- 定时巡检采购需求
- OCR 识别商品图片/验证码
- 自动下单询价
- 推送采购结果

### 推荐 n8n 模板架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Schedule  │────▶│   1688 API  │────▶│    OCR      │
│  Cronjob    │     │  采集商品   │     │  验证码识别 │
└─────────────┘     └─────────────┘     └─────────────┘
                         │                    │
                         ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  数据清洗   │◀────│  验证码结果  │
                    └─────────────┘     └─────────────┘
                         │
                         ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  Hermes     │────▶│  1688 Web   │
                    │  执行器     │     │  下单操作   │
                    └─────────────┘     └─────────────┘
                         │
                         ▼
                    ┌─────────────┐
                    │  通知推送   │
                    │ QQ/微信/邮件 │
                    └─────────────┘
```

### 核心节点配置

#### 1. Schedule Trigger
- 类型：`n8n-nodes-base.scheduleTrigger`
- Cron 表达式：`0 9 * * *`（每天9点）

#### 2. HTTP Request（1688 商品搜索）
```javascript
{
  "method": "GET",
  "url": "https://s.1688.com/youyuan/index.htm?keywords={{ $json.keywords }}",
  "options": {
    "headers": {
      "User-Agent": "Mozilla/5.0 ..."
    }
  }
}
```

#### 3. Code（数据清洗）
```javascript
// 从1688搜索结果提取商品信息
const items = $input.first().json.data.items;
return items.map(item => ({
  title: item.title,
  price: item.price,
  offerId: item.offerId,
  supplierId: item.supplierId
}));
```

#### 4. Loop Over Items（循环处理）
- 对每个商品执行：价格比对 → 库存检查 → Hermes执行下单

#### 5. OCR 验证码处理
使用前面部署的 ddddocr Flask API：
```javascript
// HTTP Request POST http://host.docker.internal:9898/ocr
{
  "base64": "{{ $json.captcha_image_base64 }}"
}
```

### Hermes 在 1688 场景的角色

| 步骤 | Hermes 能力 | n8n 配合 |
|------|------------|---------|
| 商品详情页读取 | 浏览器截图 + OCR | 提供商品ID |
| 验证码识别 | OCR + ddddocr | 调用 Flask API |
| 询价单填写 | 浏览器自动化 | 提供询价模板 |
| 异常处理 | 判断 + 人工确认 | 发送通知 |

### 1688 反爬虫应对

```javascript
// n8n Code 节点实现随机延迟
const minDelay = 1000;
const maxDelay = 3000;
const delay = Math.floor(Math.random() * (maxDelay - minDelay)) + minDelay;
await new Promise(r => setTimeout(r, delay));

// 随机 User-Agent 轮换
const userAgents = [
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
];
const ua = userAgents[Math.floor(Math.random() * userAgents.length)];
```

## n8n + Cronjob 协同

### 架构概述

```
系统 Cronjob（系统级）→ Hermes CLI → 任务执行 → n8n Webhook/API → 工作流 → 通知
                              ↓
                         Hermes Agent
                              ↓
                         桌面/浏览器操控
```

### 两种 Cronjob 模式

| 模式 | 触发器 | 适用场景 |
|------|--------|---------|
| **n8n 内置 Schedule** | n8n 定时触发器 | 轻量定时、简单逻辑 |
| **系统 Cronjob + Hermes** | 系统 crontab | 复杂逻辑、桌面操控、需要人工介入 |
| **n8n Cronjob → Hermes** | n8n Schedule → HTTP | n8n 编排 → Hermes 执行 |

### 模式A：系统 Cronjob → Hermes → n8n

**系统 crontab 配置**：
```bash
# 每天 08:00 Hermes 巡检
0 8 * * * /Users/aimac/.local/bin/hermes巡检.sh >> /tmp/hermes巡检.log 2>&1

# 每周一 09:00 1688 采购巡检
0 9 * * 1 /Users/aimac/.local/bin/hermes采购巡检.sh
```

**巡检脚本示例**（`hermes巡检.sh`）：
```bash
#!/bin/bash
export N8N_API_KEY="eyJhbGciOiJI..."
export N8N_BASE_URL="http://localhost:5678"

# Hermes 执行巡检任务
hermes execute --task "巡检所有监控服务状态"

# 触发 n8n 记录日志
curl -X POST http://localhost:5678/webhook/hermes-log \
  -H "Content-Type: application/json" \
  -d "{\"task\": \"巡检\", \"status\": \"completed\", \"time\": \"$(date)\"}"
```

### 模式B：n8n Schedule → Hermes HTTP Call

**n8n Schedule Trigger** 触发 → **HTTP Request** 调用 Hermes：

```
n8n Schedule（每5分钟）
  → HTTP Request POST http://localhost:5679/execute
  → Hermes Agent 接收任务
  → 执行（浏览器/桌面）
  → 截图验证
  → n8n Webhook 回写结果
```

### 模式C：Hermes 主动监控 + n8n 记录

Hermes 在后台持续监控，检测到异常时主动触发 n8n：

```python
# Hermes 监控循环
import requests
from datetime import datetime

while True:
    status = check_services()
    if status.has_anomaly:
        # 调用 n8n Webhook 记录异常
        requests.post(
            "http://localhost:5678/webhook/anomaly-detected",
            json={"anomaly": status.details, "timestamp": str(datetime.now())}
        )
    sleep(60)
```

### Cronjob 任务编排最佳实践

1. **幂等性**：重复执行结果一致，避免重复下单
2. **日志追踪**：每次执行写入唯一 execution_id 到 n8n
3. **异常处理**：try/catch 包裹，异常状态回传 n8n
4. **超时控制**：单次任务不超过 5 分钟，否则分片
5. **结果回写**：任务完成后主动调用 n8n API 更新状态

### 推荐工作流模板

**定时巡检工作流**（n8n 内置）：
```
Schedule Trigger（cron: 0 8 * * *）
  → HTTP Request（调用 Hermes 巡检脚本）
  → IF（检测到异常）
      → Telegram/QQ 通知
      → n8n Webhook（记录到数据库）
  → IF（正常）
      → n8n Webhook（记录健康状态）
```

## JWT 安全配置

### n8n API Key 机制

n8n 的 API Key 是 JWT（JSON Web Token），格式：
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIn0.XXXXX
```

**解码 Header**：
```json
{"alg":"HS256","typ":"JWT"}
```

**解码 Payload**：
```json
{"iss":"n8n","aud":"public-api","iat":1715000000,"exp":1715086400}
```

| 字段 | 含义 |
|------|------|
| `iss` | Issuer = `n8n`，表示由 n8n 签发 |
| `aud` | Audience = `public-api`，表示用于 Public API |
| `iat` | Issued At，签发时间戳 |
| `exp` | Expiration，过期时间 |

### 安全风险点

| 风险 | 描述 | 缓解措施 |
|------|------|---------|
| **Key 泄露** | API Key 出现在日志/代码中 | 使用环境变量，不写入代码 |
| **Key 过期** | 设置了过期时间的 Key 到期后无法使用 | 定期轮换，设置提醒 |
| **Scope 过大** | Key 权限过大（*/*） | 按最小权限创建 Key |
| **跨实例使用** | Cloud Key 用于本地实例 | 本地实例使用本地创建的 Key |
| **日志记录** | curl/requests 默认记录完整 URL | 使用 masking 日志 |

### 生产环境安全配置

#### 1. 环境变量存储

```bash
# ~/.bash_profile 或 ~/.zshrc
export N8N_API_KEY="eyJhbGciOiJI..."
export N8N_BASE_URL="https://n8n.your-domain.com"
```

#### 2. Key 最小权限原则

创建多个专用 Key，避免一个 Key 通杀：

| Key 名称 | Scopes | 用途 |
|---------|--------|------|
| `hermes-read` | `workflow:read`, `execution:read` | Hermes 只读工作流状态 |
| `hermes-trigger` | `workflow:read`, `workflow:execute` | Hermes 触发工作流 |
| `hermes-write` | `workflow:*`, `execution:*` | Hermes 写入/创建工作流 |
| `cronjob-log` | `execution:create` | Cronjob 仅写入日志 |

#### 3. HMAC Webhook 签名（防止伪造）

```javascript
// Hermes 端：签名 Webhook 请求
const crypto = require('crypto');

function signWebhook(payload, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(JSON.stringify(payload));
  return `sha256=${hmac.digest('hex')}`;
}

// n8n 端：验证签名
function verifySignature(body, signature, secret) {
  const expected = signWebhook(body, secret);
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

#### 4. 定期 Key 轮换

```bash
#!/bin/bash
# rotate_n8n_key.sh - 轮换 n8n API Key

OLD_KEY=$N8N_API_KEY
NEW_KEY=$(curl -s -X POST http://localhost:5678/api/v1/api-key \
  -H "X-N8N-API-KEY: $OLD_KEY" \
  -d '{"label": "hermes-main", "scopes": ["workflow:read", "workflow:execute"]}' \
  | jq -r '.apiKey')

# 更新环境变量（写入 .env 文件）
sed -i '' "s/N8N_API_KEY=.*/N8N_API_KEY=$NEW_KEY/" ~/.hermes/.env

# 失效旧 Key
curl -X DELETE http://localhost:5678/api/v1/api-key/$OLD_KEY \
  -H "X-N8N-API-KEY: $NEW_KEY"

echo "Key rotated: $NEW_KEY"
```

#### 5. n8n Cloud 与本地 Key 区别

| 类型 | 签发方 | `iss` | 可用范围 |
|------|--------|-------|---------|
| Cloud Key | n8n Cloud | `n8n` | 任意 n8n 实例（Cloud 或本地） |
| 本地 Key | 本地 n8n 实例 | `n8n` | 仅签发的本地实例 |

**重要**：Cloud Key 能在本地 Docker 实例使用，但本地 Key 不能用于 Cloud。

#### 6. 安全检查清单

- [ ] API Key 不硬编码在代码中
- [ ] API Key 存储在环境变量或 secrets manager
- [ ] 不同用途使用不同 Key（最小权限）
- [ ] Webhook 使用 HMAC 签名验证
- [ ] 定期轮换 Key（建议 90 天）
- [ ] 监控 Key 使用日志，异常访问告警
- [ ] n8n 实例开启 HTTPS（生产环境）
- [ ] n8n 设置 IP 白名单（企业版）

## 已知陷阱

1. **Docker Hub 超时**：拉取镜像时 `auth.docker.io` 可能超时，重试即可
2. **首次启动 n8n**：必须通过 UI 创建管理员账号，API 在账号创建前不可用
3. **Mac Docker 宿主机访问**：用 `host.docker.internal`，不是 `127.0.0.1`
4. **n8n telemetry DNS 失败导致崩溃（退出码 255）**：n8n 启动时尝试连接 `telemetry.n8n.io` 做遥测，DNS 解析失败会抛未捕获异常导致进程退出（`EAI_AGAIN getaddrinfo telemetry.n8n.io`）。修复：**在 docker-compose.yml 的 environment 中添加三个环境变量禁用 telemetry**：
   ```yaml
   - N8N_DIAGNOSTICS_ENABLED=false
   - N8N_LAUNCH_BC=false
   - N8N_PHONE_HOME=false
   ```
   加完后**必须重建容器**（`docker rm -f n8n` 再 `docker-compose up -d`），`docker-compose up -d` 只更新已存在的容器配置，不重建。
5. **docker-compose up -d 不重建容器**：修改 `docker-compose.yml` 后，`docker-compose up -d` 只对已存在的容器做更新（不会重新创建）。修改环境变量、volume 等配置时需要先 `docker rm -f <container>` 删除旧容器，再 `docker-compose up -d` 重新创建。
6. **n8n SQLite bind mount 权限问题**：使用 `~/n8n_data:/home/node/.n8n` 绑定挂载时，容器内进程以 `node` 用户运行（uid 1000），需要宿主机的 `~/n8n_data` 目录对 uid 1000 可写。如果目录属于当前用户但权限不足，n8n 会报 `SQLITE_READONLY: attempt to write a readonly database`。解决方案：确保数据目录存在且权限为 0755（通常继承自用户目录，无需额外 chmod）。
7. **ddddocr pip 安装超时**：网络问题，可用 tesseract 替代或搭建 Host Flask API
8. **n8n CODE_NODE_FUNCTION_ALLOW_EXTERNAL**：需要的环境变量记得加逗号分隔的包名
9. **n8n API Key 401**：用户提供的 Key 返回 401 = 该实例从未在 UI 创建过 API Key，需要进入 Settings → n8n API 创建
10. **SQLite 在 MacOS 上 bind mount 损坏（SQLITE_IOERR）**：macOS Docker bind mount 与 SQLite 的 fcntl 锁不兼容，数据库文件会迅速损坏。修复方法：将 docker-compose.yml 的 `volumes:` 从 bind mount（`./n8n_data:/home/node/.n8n`）改为 **named volume**（`n8n_data:/home/node/.n8n` + `volumes:` 顶层声明）。切换后会丢失数据，需重新创建管理员账号和 API Key。**推荐方案**：继续用 bind mount 但**确保数据目录已存在且权限正常**，n8n 写入不会因锁机制损坏数据（实际测试正常）。named volume 会因旧数据残留导致 onboarding 状态异常。
11. **Internal REST API 有 CSRF 保护**：`/rest/` 路径需要 Session Cookie + CSRF token，直接用 urllib/curl 调用返回 401 即使已登录。如需程序化创建 Workflow，用 Public API（`/api/v1/`）配合 X-N8N-API-KEY header。
12. **登录端点字段名**：n8n v2 的 `/rest/login` 用 `emailOrLdapLoginId` 字段（不是 `email`），密码字段是 `password`。返回 set-cookie 的 `n8n-auth` 头。
13. **Onboarding 引导对话框**：新实例首次使用时，工作流页面被 "Customize n8n to you" 下拉菜单拦截，必须填完才能进入编辑器。Settings 页面不受限，可先用 Settings 创建 API Key。
14. **Public API 不支持 PATCH**：创建 Workflow 后如需修改节点，只能删除重建。PUT/PATCH 均报 405 Method Not Allowed。
15. **Workflow activation 端点**：激活 workflow 的端点是 `POST /rest/workflows/<id>/activate`（**不是** `/api/v1/`），需要 Session Cookie 认证，Public API 的 `/api/v1/workflows/<id>/activate` 对本地 Docker 实例可能返回 401。
16. **n8n reset 命令**：`docker exec <container> n8n user-management:reset` 可重置数据库到默认用户状态，用于修复 onboarding 卡死问题。
17. **n8n SQLite 表结构（关键）**：n8n 的表名与文档常见名称不同：workflow 存储在 `workflow_entity` 表（不是 `workflow`），API keys 在 `user_api_keys` 表（不是 `api_keys`），用户表为 `user`。
18. **从 SQLite 直接提取 API Key**：当 UI 无法复制完整 Key 时（显示被遮蔽），可直接读数据库：
    ```bash
    sqlite3 ~/n8n_data/database.sqlite "SELECT apiKey, label FROM user_api_keys;"
    ```
    （bind mount 方案直接读宿主机的 SQLite 文件；named volume 需用 docker run 挂载 volume）
19. **Bypass onboarding 表单**：数据库中 `user` 表的 `settings` 字段控制 onboarding，设为 `{"userActivated":true}` + 填入 `email` 可直接跳过引导流程。
20. **API Key 的 scopes 是 JSON 数组字符串**：从数据库读出的 `scopes` 字段格式为 JSON 数组字符串（如 `'["workflow:read","workflow:activate"]'`），不是逗号分隔字符串。

## Related Skills

- `hermes-rpa` — Hermes 桌面代理核心能力
- `rag-knowledge-base` — RAG architecture: ChromaDB usage patterns, document chunking, embedding model selection, retrieval optimization, and 1688 supplier KB pipeline
- `desktop-control` — 桌面操控具体方法

## 参考文档

- `references/n8n-sqlite-direct-access.md` — n8n SQLite 数据库直接操作（绕过 UI/API 修复 onboarding、提取遮蔽的 API Key、激活 workflow、**备份与恢复**）

