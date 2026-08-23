# Gateway 代理配置 + DNS 劫持排查（2026-07-16）

## 故障现象
Hermes App 提示「提示词发送失败」

## 根因
两层问题叠加：
1. Gateway 随机端口（`--port 0`）导致 App 缓存端口过时
2. 网络层：出口 HTTPS 被透明拦截，SSL_ERROR_SYSCALL

## 排查路径

### Step 1：确认 Gateway 端口
```bash
# gateway 进程在跑但端口随机
ps aux | grep 'hermes_cli.main serve' | grep -v grep
# 输出类似：
# kk 45103 ... python -m hermes_cli.main serve --host 127.0.0.1 --port 0
# port 0 = 随机分配，需要固定

# 验证端口是否 LISTEN（lsof 可能漏看，用 netstat）
netstat -an | grep 18281 | grep LISTEN
# 或
fuser 18281/tcp
```

### Step 2：确认网络是否通
```bash
# 直接测 — 不走代理
curl -sS -m 15 -o /dev/null -w "%{http_code}" https://inference-api.nousresearch.com/v1/models
# 失败返回 SSL_ERROR_SYSCALL = 出口被拦截

# 看 DNS 是否被劫持
dig +short inference-api.nousresearch.com
# 返回 172.19.0.x = DNS 劫持到内网，真实出口 IP 被墙
```

### Step 3：找代理端口
Clash Mi 有两个不同端口：
- **本地面板端口**：Clash Mi UI 控制端口（如 63900/7066），不是代理
- **HTTP(S) 代理端口**：真正的 HTTP 代理，在 Clash Mi 设置 → 代理设置 里找

```bash
# 列出所有 Clash 相关监听端口
lsof -n -P | grep -i clash
```

### Step 4：设代理重启 Gateway
```bash
# 必须写在同一条命令里，进程启动时读取环境变量
https_proxy=http://127.0.0.1:<代理端口> \
http_proxy=http://127.0.0.1:<代理端口> \
all_proxy=http://127.0.0.1:<代理端口> \
  /Users/kk/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main serve \
    --host 127.0.0.1 --port 18281
```

### Step 5：验证代理是否生效
```python
import urllib.request, os

proxy = "http://127.0.0.1:7066"
try:
    proxy_handler = urllib.request.ProxyHandler({
        "http": proxy, "https": proxy
    })
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request("https://inference-api.nousresearch.com/v1/models")
    with opener.open(req, timeout=15) as r:
        print(f"OK: {r.status}")
except Exception as e:
    print(f"Failed: {e}")
```

## 关键教训
- `https_proxy` 环境变量只在该进程启动时读取一次
- 启动后改 shell 环境变量不影响已运行的进程
- Clash Mi 本地面板端口 ≠ HTTP 代理端口，必须单独找
- DNS 劫持到内网 172.19.x.x 是出口风控现象，DoH 也被拦截时无本地绕行方法，需依赖代理
