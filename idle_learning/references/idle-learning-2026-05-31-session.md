# Idle Learning 2026-05-31 Session

**方向**：执行层 — screen_watcher 链路持续监控 + 本地模型状态

## 核心发现

### 1. screen_watcher 链路持续正常
- 进程 PID 3176（screen_watcher.py）持续运行
- screenshots/current.png 每分钟更新（00:24 最新）
- AUTO-EXEC-DRY 日志 306 条，handler 冷却中正常运行

### 2. HN Firebase API 稳定可用
- news.ycombinator.com blocked，但 firebase API 正常（200 OK）
- Top story 2026-05-31: Anthropic surpasses OpenAI (281pts)
- 其他热门：Zig Build System Reworked (237pts)、Openrsync (148pts)、Voxel Space (76pts)

### 3. Ollama 远程库 Vision 模型状态（2026-06-02 重大发现）
- `api.ollama.com` 可访问（200 OK）
- 远程库 vision 相关模型仅 2 个：qwen3-vl:235b-instruct、qwen3-vl:235b（437GB，均超大）
- **⚠️ 社区模型完全缺失**：smolvlm2-agentic-gui、qwen3-vl:2b、llama3.2-vision 等均不在 api.ollama.com 列表
- `?models=vision` 参数无效
- 说明这些是社区模型，需通过 `ollama pull ahmadwaqar/smolvlm2-agentic-gui` 安装

### 4. Telegram 推送未配置
- screen_trigger_handler 检测到 TELEGRAM_BOT_TOKEN/CHAT_ID 未设置
- config.yaml 中 telegram channel 仅配置 reactions/voice，无 BOT_TOKEN
- 这是已知限制，不影响核心功能

## 技术验证命令

```bash
# 检查 screen_watcher 进程
ps aux | grep -E "screen_watcher|screen_poller|screen_trigger" | grep -v grep

# 检查截图时间
ls -lt ~/.hermes/screenshots/current.png

# 检查 dry-run 日志
grep -c "AUTO-EXEC-DRY" ~/.hermes/logs/screen_trigger.log

# 检查本地模型（curl 方式，避免 Python API 超时）
curl -s --max-time 8 http://127.0.0.1:11434/api/tags | python3 -c "
import sys,json;d=json.load(sys.stdin)
for m in d.get('models',[]): print(m['name'], '|', round(m['size']/(1024**3), 2), 'GB')
"

# 检查网络
curl -s --max-time 5 https://github.com -o /dev/null && echo "github:ok" || echo "github:blocked"
curl -s --max-time 5 https://news.ycombinator.com -o /dev/null && echo "hn:ok" || echo "hn:blocked"

# HN Firebase API 状态
curl -s --max-time 8 "https://hacker-news.firebaseio.com/v0/topstories.json" -o /dev/null -w "%{http_code}"
```

## 待解决

- github.com 仍 blocked，smolvlm2-agentic-gui 待恢复 pull
- smolvlm2 模型从本地消失两次（Ollama 自动清理？），需关注

## 下次方向

Vision — 调研替代视觉模型（qwen2.5vl 或 llama3.2-vision），github 恢复后重新拉取 smolvlm2
