---
name: network-intercept
description: mitmproxy-mcp network interception — mock/stub/spy HTTP requests via MCP protocol. 触发：mock http request / intercept network / stub api response / cy.intercept equivalent / 网络拦截 / 模拟接口返回。
triggers:
  - mock http request
  - intercept network request
  - stub api response
  - cy.intercept equivalent
  - 网络拦截
  - 模拟接口返回
---

# Network Intercept — mitmproxy-mcp 实现 `cy.intercept()`

用 mitmproxy-mcp（官方 MCP Server）拦截/修改/模拟浏览器的网络请求。

## 架构

```
Browser → mitmproxy (localhost:8080) → Real Server
              ↓
       mitmproxy-mcp (MCP Server)
              ↓
       Hermes (MCP Client) ← 你在这里调工具
```

**对比手写脚本**：mitmproxy-mcp = 官方维护的 MCP 封装，流量录制/重放/JSONPath 提取开箱即用，无需自己写 Addon 类。

## 安装

```bash
# 依赖 Python 3.14（macOS 系统 Python）
pip install mitmproxy-mcp --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# mitmdump PATH 警告时加到 .zshrc
export PATH="/Library/Frameworks/Python.framework/Versions/3.14/bin:$PATH"
```

验证：
```bash
mitmdump --version
python3 -c "import mitmproxy_mcp; print('OK')"
```

## MCP Server 配置

在 `~/.hermes/config.yaml` 加一段，让 Hermes 启动时自动加载 mitmproxy-mcp：

```yaml
mcp_servers:
  mitmproxy:
    command: mitmproxy-mcp
    env: {}
    # 或者用绝对路径：
    # command: /Library/Frameworks/Python.framework/Versions/3.14/bin/mitmproxy-mcp
```

配置完需 `hermes gateway restart`。

## 工具清单（全部是 `@mcp.tool()`）

### 代理生命周期

| 工具 | 用途 |
|---|---|
| `start_proxy(port=8080)` | 启动 mitmproxy 代理 |
| `stop_proxy()` | 停止代理 |
| `get_traffic_summary(limit=20)` | 列出最近 N 条捕获流量（摘要） |
| `inspect_flow(flow_id)` | 查看某条流量的完整请求/响应 |
| `clear_traffic()` | 清空捕获记录 |

### 拦截规则

| 工具 | 用途 |
|---|---|
| `add_intercept_rule(rule_id, url_pattern, phase, action_type, ...)` | 添加拦截规则 |
| `list_rules()` | 查看当前所有活跃规则 |
| `clear_rules()` | 清空所有规则 |

### 流量提取与重放

| 工具 | 用途 |
|---|---|
| `extract_from_flow(flow_id, json_path, css_selector)` | 用 JSONPath 或 CSS 从响应体提数据 |
| `replay_flow(flow_id, method, headers, body)` | 重放历史请求 |

### 全局 Header 注入

| 工具 | 用途 |
|---|---|
| `set_global_header(key, value)` | 全局注入请求头（所有请求） |
| `remove_global_header(key)` | 删除全局请求头 |

### 域名白名单

| 工具 | 用途 |
|---|---|
| `set_scope(allowed_domains)` | 只拦截特定域名，其他 bypass |

---

## 典型用法

### 1. Mock 某个 API 返回固定数据

```python
# Step 1: 启动代理
start_proxy(port=8080)

# Step 2: 添加 mock 规则
add_intercept_rule(
    rule_id="mock_user",
    url_pattern="**/api/user**",
    phase="response",          # 拦截响应
    action_type="replace_body",
    value='{"id": 1, "name": "test"}',
    search_pattern=".*"        # 替换整个 body
)

# Step 3: 浏览器访问 → 自动被 mock
# navigate("https://target-site.com/profile")

# Step 4: 查看流量
get_traffic_summary(limit=10)

# Step 5: 清理规则
clear_rules()
stop_proxy()
```

### 2. Spy + Wait（类似 `cy.wait('@login')`）

mitmproxy-mcp 没有直接的 wait 工具，用轮询实现：

```python
# 等待某个请求出现（poll 方式）
import time
for _ in range(20):
    result = get_traffic_summary(limit=50)
    if '"url":"/api/login"' in result or '"path":"/api/login"' in result:
        print("Login request captured!")
        break
    time.sleep(0.5)
else:
    raise TimeoutError("Login request never appeared")
```

### 3. 修改真实响应内容

```python
# 把响应里的 name 字段改成 "hacked"
add_intercept_rule(
    rule_id="replace_name",
    url_pattern="**/api/user**",
    phase="response",
    action_type="replace_body",
    search_pattern='"name": "[^"]*"',
    value='"name": "hacked"'
)
```

### 4. Block 某个请求

```python
add_intercept_rule(
    rule_id="block_ads",
    url_pattern="**/ads/**",
    phase="request",
    action_type="block"
)
```

### 5. 全局注入 Header（测试需要 Auth 的接口）

```python
set_global_header(key="Authorization", value="Bearer test-token-123")
# 所有请求都会带上这个 header
remove_global_header(key="Authorization")  # 用完删除
```

### 6. 只拦截特定域名

```python
set_scope(allowed_domains=["api.target-site.com", "cdn.target-site.com"])
# 其他域名流量直接放行，不记录
```

### 7. 从响应体提取数据（JSONPath）

```python
# 先拿到 flow_id（从 get_traffic_summary 里找）
# 然后用 JSONPath 提取
extract_from_flow(
    flow_id="abc123",
    json_path="$.data.items[*].name"
)
# 返回提取到的值列表
```

### 8. 重放历史请求（调试）

```python
replay_flow(
    flow_id="abc123",
    method=None,      # None = 用原始 method
    headers=None,     # None = 用原始 headers
    body=None         # None = 用原始 body
)
```

---

## E2E Testing 集成（spec 格式）

```yaml
name: 搜索功能测试

before:
  - action: mitm_start
    port: 8080

  - action: mitm_mock
    rule_id: mock_search
    url_pattern: "**/api/search**"
    phase: response
    action_type: replace_body
    value: '{"results": [{"id": 1, "name": "mocked result"}]}'
    search_pattern: ".*"

steps:
  - action: navigate
    url: http://example.com

  - action: type
    selector: "#q"
    text: "test"

  - action: click
    selector: "button[type=submit]"

  - action: mitm_wait
    pattern: "**/api/search**"
    timeout: 5000

  - action: assert_text
    selector: ".results"
    expected: "mocked result"

after:
  - action: mitm_clear
  - action: mitm_stop
```

对应的 e2e-testing step handlers：

```python
# mitm_start
start_proxy(port=step.get("port", 8080))

# mitm_mock
add_intercept_rule(
    rule_id=step["rule_id"],
    url_pattern=step["url_pattern"],
    phase=step.get("phase", "response"),
    action_type=step["action_type"],
    value=step.get("value"),
    search_pattern=step.get("search_pattern"),
)

# mitm_wait（轮询实现）
import time, json
for i in range(int(step["timeout"]) // 500):
    summary = get_traffic_summary(limit=50)
    if step["pattern"] in summary:
        break
    time.sleep(0.5)
else:
    raise TimeoutError(f"Pattern {step['pattern']} not found in traffic")

# mitm_clear
clear_rules()

# mitm_stop
stop_proxy()
```

---

## 已知限制

| 限制 | 说明 |
|---|---|
| **HTTPS** | 首次需要把 `~/.mitmproxy/mitmproxy-ca-cert.pem` 导入系统信任区 |
| **HTTP/3 (QUIC)** | mitmproxy 不支持，流量会 bypass 代理 |
| **移动端** | CA 证书要装到设备上 |
| **wait 实现** | mitmproxy-mcp 没有原生 wait，需自己轮询 `get_traffic_summary` |
| **Python 版本** | mitmproxy-mcp 需要 Python 3.14，macOS 系统 Python 3.11 不兼容 |

---

## 手写脚本 vs mitmproxy-mcp

| | 手写脚本（已废弃） | mitmproxy-mcp |
|---|---|---|
| 协议 | 私有 HTTP API | 标准 MCP（任何 MCP Host 都能调） |
| 流量录制/重放 | ❌ 无 | ✅ 有 |
| JSONPath 提取 | ❌ 无 | ✅ 有 |
| CSS 提取 | ❌ 无 | ✅ 有 |
| 全局 Header 注入 | 需手写 | ✅ `set_global_header` |
| 域名白名单 | 需手写 | ✅ `set_scope` |
| 安装维护 | 自己维护 | 官方更新 |

旧脚本 `scripts/mock_handler.py` / `controller.py` / `mitm_client.py` 已废弃，可删除。
