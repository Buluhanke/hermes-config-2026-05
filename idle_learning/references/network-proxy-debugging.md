# 代理与网络诊断

## 当前环境代理配置

- Clash Verge MH (verge-mihomo) 监听：**7897/tcp**（HTTP 代理）
- 代理应用：Clash Verge（不归属通讯渠道，可检查/修复）
- 代理路径：`~/.hermes/proxy-env.sh`（手动设置proxy环境变量的临时脚本）

### 常用检测命令

```bash
# 测试 github.com（直连测试）
curl -s --max-time 5 https://github.com -o /dev/null -w "%{http_code}"

# 测试 HN.com（需要代理）
curl -s --max-time 5 https://news.ycombinator.com -o /dev/null -w "%{http_code}"

# 测试代理是否可达
curl -s --max-time 5 http://127.0.0.1:7897 -o /dev/null -w "%{http_code}"

# 测试 Firebase API（不需要代理，直连）
curl -s --max-time 5 "https://hacker-news.firebaseio.com/v0/topstories.json" -o /dev/null -w "%{http_code}"
```

## 常见故障

### github.com blocked 但实际能通

**现象**：`curl -s --max-time 5 https://github.com -o /dev/null && echo "ok" || echo "blocked"` 报告 blocked，但单独 `curl -s --max-time 5 https://github.com -w "%{http_code}"` 返回 200。

**原因**：`&&` 和 `||` 在某些 shell 解析下有诡异行为，导致即使 curl 成功也走了 || 分支。

**处理**：用单条 curl 测试，不要用 &&/|| 链接多个命令。

### HN.com 走代理超时

**现象**：直连 curl 返回 000（超时）；代理 curl 返回 200 但 TLS handshake 后超时。

**原因**：Clash 代理节点到 HN 的路由问题，或节点本身到 HN 延迟高。

**处理**：
1. 检查 Clash 控制台确认代理规则配置
2. 尝试切换代理节点
3. 降级走 Firebase API（`hacker-news.firebaseio.com`，直连可用）
4. 不动 Clash 配置（归属通讯渠道，等用户确认）

### 代理环境变量不生效

**现象**：设置了 `HTTP_PROXY=http://127.0.0.1:7897` 但 curl 仍直连。

**排查步骤**：
1. 确认变量已设置：`echo $HTTPS_PROXY`
2. 检查是否被 NO_PROXY 绕过了：HN 不在 NO_PROXY 列表里
3. 确认代理进程在跑：`ps aux | grep clash`
4. 确认端口正确：`lsof -i :7897`

**Hermes terminal 配置**：
- `hermes config set terminal.env_passthrough "HTTP_PROXY,HTTPS_PROXY,http_proxy,https_proxy,NO_PROXY,no_proxy"`
- `hermes config set terminal.shell_init_files "[\"~/.zshrc\"]"`

⚠️ `.zshrc` 和 `config.yaml` 是受保护文件，不能直接写。必须用 `hermes config set` 命令修改。

## 核心原则

发现问题 → 立刻诊断 → 解决再继续。不跳过，不绕行，不等授权。