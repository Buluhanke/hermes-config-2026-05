---
name: n8n-hermes-integration
description: n8n 工作流自动化平台与 Hermes Desktop Agent 的集成架构。涵盖 n8n + ChromaDB Docker 部署、Ollama/LLM 连接、ddddocr 验证码集成、工作流设计模式。
triggers:
  - n8n 部署安装
  - n8n 工作流设计
  - ChromaDB 向量库连接
  - n8n OCR 验证码破解
  - n8n + Hermes 联动
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
    volumes:
      - ./n8n_data:/home/node/.n8n
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

## 当前运行状态（2026-05-15更新）
- n8n容器：`hermes-ai-n8n-1`，端口5678已就绪
- Docker Desktop已启动（之前未开机导致docker API无法连接）
- n8n数据卷：使用named volume `n8n_data`（避免SQLite bind mount损坏）
- 主动触发系统：cronjob每日08:00触发Hermes巡检 → QQ推送

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

## 已知陷阱

1. **Docker Hub 超时**：拉取镜像时 `auth.docker.io` 可能超时，重试即可
2. **首次启动 n8n**：必须通过 UI 创建管理员账号，API 在账号创建前不可用
3. **Mac Docker 宿主机访问**：用 `host.docker.internal`，不是 `127.0.0.1`
4. **ddddocr pip 安装超时**：网络问题，可用 tesseract 替代或搭建 Host Flask API
5. **n8n CODE_NODE_FUNCTION_ALLOW_EXTERNAL**：需要的环境变量记得加逗号分隔的包名
6. **n8n API Key 401**：用户提供的 Key 返回 401 = 该实例从未在 UI 创建过 API Key，需要进入 Settings → n8n API 创建
7. **SQLite 在 MacOS 上 bind mount 损坏（SQLITE_IOERR）**：macOS Docker bind mount 与 SQLite 的 fcntl 锁不兼容，数据库文件会迅速损坏。修复方法：将 docker-compose.yml 的 `volumes:` 从 bind mount（`./n8n_data:/home/node/.n8n`）改为 **named volume**（`n8n_data:/home/node/.n8n` + `volumes:` 顶层声明）。切换后会丢失数据，需重新创建管理员账号和 API Key。
8. **Internal REST API 有 CSRF 保护**：`/rest/` 路径需要 Session Cookie + CSRF token，直接用 urllib/curl 调用返回 401 即使已登录。如需程序化创建 Workflow，用 Public API（`/api/v1/`）配合 X-N8N-API-KEY header。
9. **登录端点字段名**：n8n v2 的 `/rest/login` 用 `emailOrLdapLoginId` 字段（不是 `email`），密码字段是 `password`。返回 set-cookie 的 `n8n-auth` 头。
10. **Onboarding 引导对话框**：新实例首次使用时，工作流页面被 "Customize n8n to you" 下拉菜单拦截，必须填完才能进入编辑器。Settings 页面不受限，可先用 Settings 创建 API Key。
11. **Public API 不支持 PATCH**：创建 Workflow 后如需修改节点，只能删除重建。PUT/PATCH 均报 405 Method Not Allowed。
12. **Workflow activation 端点**：激活 workflow 的端点是 `POST /rest/workflows/<id>/activate`（**不是** `/api/v1/`），需要 Session Cookie 认证，Public API 的 `/api/v1/workflows/<id>/activate` 对本地 Docker 实例可能返回 401。
13. **n8n reset 命令**：`docker exec <container> n8n user-management:reset` 可重置数据库到默认用户状态，用于修复 onboarding 卡死问题。
14. **n8n SQLite 表结构（关键）**：n8n 的表名与文档常见名称不同：workflow 存储在 `workflow_entity` 表（不是 `workflow`），API keys 在 `user_api_keys` 表（不是 `api_keys`），用户表为 `user`。
15. **从 SQLite 直接提取 API Key**：当 UI 无法复制完整 Key 时（显示被遮蔽），可通过 Python 容器直接读数据库：
    ```bash
    docker run --rm -v <n8n_named_volume>:/data python:3.11 -c "
    import sqlite3, json
    db = sqlite3.connect('/data/database.sqlite')
    db.row_factory = sqlite3.Row
    keys = db.execute('SELECT * FROM user_api_keys').fetchall()
    for k in keys: print(k['apiKey'])
    "
    ```
    named volume 名称从 `docker volume ls` 查看（格式 `hermes-ai_n8n_data`）。
16. **Bypass onboarding 表单**：数据库中 `user` 表的 `settings` 字段控制 onboarding，设为 `{"userActivated":true}` + 填入 `email` 可直接跳过引导流程。
17. **API Key 的 scopes 是 JSON 数组字符串**：从数据库读出的 `scopes` 字段格式为 JSON 数组字符串（如 `'["workflow:read","workflow:activate"]'`），不是逗号分隔字符串。

## 相关技能

- `hermes-rpa` — Hermes 桌面代理核心能力
- `desktop-control` — 桌面操控具体方法

## 参考文档

- `references/n8n-sqlite-direct-access.md` — **新增：n8n SQLite 数据库直接操作**（绕过 UI/API 修复 onboarding、提取遮蔽的 API Key、激活 workflow）

