# Telegram Pool Timeout — 根因分析与修复（2026-06-04）

## 症状
日志持续出现：
```
telegram.error.TimedOut: Pool timeout: All connections in the connection pool are occupied.
```
连续 10 次重连失败，每次间隔指数退避（5s → 10s → 20s → 40s → 60s）。

## 根因（双重）

### 根因1：Telegram 平台 request_kwargs 配置过大
`gateway/platforms/telegram.py` 第 1562 行：
```python
"connection_pool_size": _env_int("HERMES_TELEGRAM_HTTP_POOL_SIZE", 50),
```
默认值 512（从 telegram.py 全局设置继承），但 Hermes 有 5 个 platform 并发运行（telegram/qqbot/weixin/feishu/api_server），每个都建 512 socket 连接池 → 远超 macOS 默认 fd 限制（256 软限制）。

### 根因2：5处临时 AsyncClient 反复创建连接池
`send_message_tool.py` 4 处 + `ntfy` 1 处每次调用都 `async with httpx.AsyncClient(...)` 新建连接池，高并发时 TLS 握手累积大量 CLOSE_WAIT，连接无法及时归还。

## 修复

### 修复1：.env 参数（立即生效，重启后加载）
```
# Telegram HTTP 池大小（512→30，防止 fd 占满）
HERMES_TELEGRAM_HTTP_POOL_SIZE=30
# Pool 超时（秒）
HERMES_TELEGRAM_HTTP_POOL_TIMEOUT=12.0
# 长回复读写超时
HERMES_TELEGRAM_HTTP_READ_TIMEOUT=40.0
HERMES_TELEGRAM_HTTP_WRITE_TIMEOUT=15.0

# 共享 HTTP 客户端全局限制
HERMES_GATEWAY_HTTPX_MAX_CONNECTIONS=40
HERMES_GATEWAY_HTTPX_MAX_KEEPALIVE=8
HERMES_GATEWAY_HTTPX_TIMEOUT_READ=15.0
HERMES_GATEWAY_HTTPX_TIMEOUT_CONNECT=5.0
HERMES_GATEWAY_HTTPX_TIMEOUT_POOL=8.0
```

### 修复2：_shared_http_client.py 模块级单例
新建 `gateway/platforms/_shared_http_client.py`，替换 5 处临时 client 为共享连接池。

### 修复3：self_evolution.sh 增强巡检
- 告警阈值从 5 次降到 3 次（提前介入）
- 代理正常但 Telegram 仍报错 → 写 `telegram,pool,httpx,alert` fact 到 memory_store

## 避坑规则（永久生效）
1. **connection_pool_size 永远不要 > 50**（所有 platform 共享）
2. **不要新建临时 AsyncClient**，统一走 shared_http_client
3. **pool_timeout 不要 < 8s**，否则网络抖动会误触发
4. **read_timeout 长回复场景至少 35s**
5. **修复后必须文档化**（本次修复写入本文件和 SOUL.md）

## 自检命令
```bash
# 检查当前连接数
lsof -i :9333 | wc -l
# 检查 gateway 日志中的 pool timeout
grep "Pool timeout" ~/.hermes/logs/gateway.log | wc -l
# 检查 fd 使用
launchctl limit maxfiles
```