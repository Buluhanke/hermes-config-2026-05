# Gateway 随机端口导致 App "提示词发送失败"（2026-07-16）

## 症状
Hermes App 提示"提示词发送失败"，但 gateway 进程（`hermes_cli.main serve`）实际在运行。

## 根因
Gateway 用 `--port 0` 随机分配端口（如 57221），但 Hermes App 缓存了旧端口（如 18281），导致连接被 Refused。

## 诊断路径
```bash
# 1. 确认 gateway 进程在跑
ps aux | grep 'hermes_cli.main serve' | grep -v grep

# 2. 查看 gateway 监听的实际端口
#    lsof 可能漏看，用 netstat/fuser
netstat -an | grep <port> | grep LISTEN
fuser <port>/tcp

# 3. 检查 App 连接的是哪个端口
#    App 会缓存上次成功连接的端口，重启后旧端口仍被使用
```

## 修复步骤
```bash
# 1. 找到旧 gateway PID
ps aux | grep 'hermes_cli.main serve' | grep -v grep | awk '{print $2}'

# 2. kill 旧进程
kill <pid>

# 3. 用固定端口重启
/Users/kk/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main serve --host 127.0.0.1 --port 18281

# 4. 验证（用 netstat，lsof 可能漏看）
netstat -an | grep 18281 | grep LISTEN
# 期望：tcp4  0  0  127.0.0.1.18281  *.*  LISTEN
```

## 附加发现
本次同时发现外部 HTTPS 全断（SSL_ERROR_SYSCALL，Google/GitHub 超时），Clash Mi 代理也不通。需先解决网络问题才能让 gateway 真正完成请求。
