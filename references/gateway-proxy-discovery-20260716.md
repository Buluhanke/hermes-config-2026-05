# Gateway 代理出口发现路径（2026-07-16）

## 问题
terminal 无法直连外网（HTTPS SSL_ERROR_SYSCALL / connection timeout），但浏览器（Chrome）正常打开网站。gateway 进程因此无法访问 Nous Portal / inference-api。

## 根因
Clash Mi 运行在 TUN 模式（系统级透明代理），浏览器流量自动走代理，但 terminal 的 HTTP 流量默认直连。被 DNS 劫持到内网 172.19.0.x 后，SSL 握手在出口被阻断。

## 发现路径（关键新方法）

不是本地端口扫描，而是查系统级代理配置：

```bash
# Step 1：查 macOS 系统级 HTTP 代理设置
networksetup -getwebproxy Wi-Fi
# 输出示例：
# Enabled: No
# Server: 192.168.0.110
# Port: 7890

# Step 2：验证代理 IP:端口是否可通
nc -z -w 3 192.168.0.110 7890 && echo "open"

# Step 3：验证代理是否真正可用（用目标 API）
curl -sS -m 15 -o /dev/null -w "%{http_code}" \
  --proxy http://192.168.0.110:7890 \
  https://inference-api.nousresearch.com/v1/models
# 返回 200 即代理可用
```

## 重要区别

| 端口类型 | 示例 | 用途 |
|---------|------|------|
| Clash Mi 本地面板端口 | 63900, 7066 | 控制/UI 界面，非代理 |
| 系统代理（局域网） | 192.168.0.110:7890 | 真正的 HTTP 出口代理 |

## 修复操作

确认代理可用后，重启 gateway 加代理环境变量：

```bash
# 找 gateway PID
ps aux | grep 'hermes_cli.main serve' | grep -v grep | awk '{print $2}'

# 杀掉
kill <pid>

# 用代理环境变量重启（注意：加在命令前，进程启动后无效）
https_proxy=http://192.168.0.110:7890 \
http_proxy=http://192.168.0.110:7890 \
all_proxy=http://192.168.0.110:7890 \
  /Users/kk/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main serve \
  --host 127.0.0.1 --port 18281
```

## 验证

```bash
# gateway 自身可访问外网
curl -sS -m 15 -o /dev/null -w "%{http_code}" \
  --proxy http://192.168.0.110:7890 \
  https://inference-api.nousresearch.com/v1/models
# 应返回 200
```
