# gateway-restart-technique 参考：2026-08-03 实操记录

## 背景
用户问"你可以通过终端命令重启网关的，为什么每次你都要来问我？"
→ 触发点：我每次遇到 gateway 重启需求就绕圈子，而不是直接执行。

## 本次操作链

### 1. 修改 PenPot MCP 配置（enabled: false → 删除条目）

```python
import yaml
cfg = yaml.safe_load(open('/Users/aimac/.hermes/config.yaml'))
del cfg['mcp_servers']['penpot']   # 完整删除，不是设 false
yaml.dump(cfg, open('/Users/aimac/.hermes/config.yaml','w'))
```

### 2. computer_use 重启 gateway

步骤：
- capture Terminal app → 找到独立的 `-zsh` 标签（元素 352：`AXRadioButton "~ — -zsh"`）
- click 352 切换标签
- type `launchctl kickstart -k ai.hermes.gateway`
- key return 发回车
- 等待 KeepAlive 自动拉起新进程

验证：
```bash
# 确认新 PID（08:16AM 启动，区别于旧 00:19）
ps aux | grep "gateway run --replace" | grep -v grep
# 新 PID = 35924

# 确认 penpot 警告停止（最后一条 08:31，之后全干净）
grep "penpot" ~/.hermes/logs/agent.log | tail -3
```

## 发现

- `enabled: false` 不够：gateway 重启后 penpot 仍然尝试连接并报错（parked 状态继续重试）
- 必须删除 `mcp_servers.penpot` 整个条目
- 配置写入后 gateway 不会热重载，必须重启才能生效

## 相关文件

- config: `/Users/aimac/.hermes/config.yaml`
- logs: `~/.hermes/logs/agent.log`
- launchd job: `ai.hermes.gateway`
