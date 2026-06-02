# Curl + no_proxy Pattern — 绕过 Python urllib 的代理 SSL 故障

## 问题

macOS 上 Clash 代理（默认 `http://127.0.0.1:7897`）通过 `https_proxy` 环境变量劫持所有 HTTPS 请求。Python `urllib.request.urlopen` 走代理访问某些 API（如 v2.aicodee.com）会触发：

```
[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1081)
```

或证书错误：
```
certificate verify failed: Hostname mismatch, certificate is not valid for 'v2.aicodee.com'
```

## 根因

- macOS 默认有 `https_proxy=http://127.0.0.1:7897` 环境变量
- Clash 代理是 HTTP CONNECT 隧道，对某些域名的 TLS 终结不兼容
- Python `urllib` 走代理时**无法**通过 `no_proxy=` 绕过（macOS + Python <3.13 已知问题）
- `requests` 库在 macOS 上同样存在

## 解法：用 curl subprocess 替代 urllib

curl 的 `--noproxy '*'` 标志**会**绕过系统代理，强制直连目标：

```python
import subprocess, json

def _call_via_curl(url, payload, headers, timeout=20):
    """用 curl 走 no_proxy 直连，绕过系统代理设置的 SSL 问题"""
    data = json.dumps(payload).encode()
    auth = headers.get("Authorization", "")
    cmd = [
        "curl", "-s", "--noproxy", "*", "-X", "POST", url,
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: {auth}",
        "-d", data.decode(),
        "--max-time", str(timeout)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    if result.returncode != 0:
        return None, f"curl exit {result.returncode}: {result.stderr[:80]}"
    return json.loads(result.stdout), None
```

## 验证

```bash
# 失败模式：Python urllib 走代理
python3 -c "
import os, urllib.request, json
os.environ['https_proxy'] = 'http://127.0.0.1:7897'
req = urllib.request.Request('https://v2.aicodee.com/v1/chat/completions',
    data=json.dumps({'model':'MiniMax-M2.7-highspeed','messages':[{'role':'user','content':'Hi'}],'max_tokens':10}).encode(),
    headers={'Authorization':'Bearer YOUR_KEY','Content-Type':'application/json'})
urllib.request.urlopen(req, timeout=15)  # SSL EOF
"

# 成功模式：curl --noproxy '*'
curl -s --noproxy '*' -X POST 'https://v2.aicodee.com/v1/chat/completions' \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7-highspeed","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}'
# 返回 HTTP 200 + 响应体
```

## 替代方案（不推荐）

### 方案 1：直接清空代理环境变量
```python
os.environ.pop('https_proxy', None)
os.environ.pop('http_proxy', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('HTTP_PROXY', None)
# 然后用 requests 或 urllib 直连
```
**缺点**：影响后续代码对其他代理的访问能力。

### 方案 2：自定义 HTTPSHandler + 禁用代理
```python
import urllib.request
proxy_handler = urllib.request.ProxyHandler({})  # 空代理
https_handler = urllib.request.HTTPSHandler(context=ssl.create_default_context())
opener = urllib.request.build_opener(proxy_handler, https_handler)
urllib.request.install_opener(opener)
```
**缺点**：全局副作用，可能影响其他 urllib 请求。

### 方案 3：用 httpx + trust_env=False
```python
import httpx
client = httpx.Client(trust_env=False)  # 不读环境代理
r = client.post(url, json=payload, headers=headers)
```
**缺点**：需要装 httpx；某些 HTTP 客户端行为与 urllib 略有差异。

## 最佳实践

**直接用 curl subprocess 模式**（方案 A），原因：
- 完全绕过 Python 的代理解析逻辑
- `--noproxy '*'` 行为确定，与 shell 一致
- 不需要额外依赖
- 不污染全局环境
- subprocess.run() 进程隔离，干净退出

## 适用场景

- macOS + Clash 代理 + 任何 Python HTTP 客户端
- Linux + 系统代理 + Python
- Docker 容器内 + host 代理转发
- 任何"curl 能通 Python 死活不通"的场景

## 反向场景：有些 API 反而要走代理

某些 API（公司内网、地区限制 API）**必须**走代理才通。判断标准：
- `curl --noproxy '*' URL` 失败 + `curl URL` 成功 → 必须走代理，用 urllib
- `curl URL` 失败 + `curl --noproxy '*' URL` 成功 → 走代理 SSL 有问题，用 curl 模式

## 实际案例（reactor_v3.py）

```python
def _call_via_curl(url, payload, headers, timeout=20):
    """用 curl 走 no_proxy 直连，绕过系统代理设置的 SSL 问题"""
    import subprocess, json as _json
    data = _json.dumps(payload).encode()
    auth = headers.get("Authorization", "")
    cmd = [
        "curl", "-s", "--noproxy", "*", "-X", "POST", url,
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: {auth}",
        "-d", data.decode(),
        "--max-time", str(timeout)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        if result.returncode != 0:
            return None, f"curl exit {result.returncode}: {result.stderr[:80]}"
        resp = _json.loads(result.stdout)
        return resp, None
    except subprocess.TimeoutExpired:
        return None, "curl timeout"
    except Exception as e:
        return None, str(e)[:80]


async def call_minimax(prompt, model="MiniMax-M2.7-highspeed", max_tokens=512, timeout=20):
    """调 LLM 走 curl 模式"""
    api_key = os.environ.get("AICODEE_API_KEY") or os.environ.get("MINIMAX_CN_API_KEY", "")
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp, err = _call_via_curl(f"{BASE_URL}/chat/completions", payload, headers, timeout)
    if err:
        return None, err
    msg = resp.get("choices", [{}])[0].get("message", {})
    # 推理模型响应在 reasoning_content
    return msg.get("content") or msg.get("reasoning_content") or "", None
```
