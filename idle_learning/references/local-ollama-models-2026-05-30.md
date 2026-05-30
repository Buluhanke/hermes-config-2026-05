# 本地 Ollama 模型状态 — 2026-05-30 实测

## 验证方法

⚠️ 必须用 `127.0.0.1:11434`（本地API），不能用 `api.ollama.com`（远程库）
```bash
curl -s --max-time 10 http://127.0.0.1:11434/api/tags | python3 -c "
import json,sys
data=json.load(sys.stdin)
for m in data.get('models',[]):
    print(m['name'])
"
```

## 本地已安装模型（2026-05-30 07:47 CST）

| 模型 | 状态 | 用途 |
|------|------|------|
| ahmadwaqar/smolvlm2-agentic-gui:latest | ✅ | screen_trigger_handler 主模型，GUI专用 |
| qwen3-vl:2b | ✅ | 离线OCR备选（主场景分析超时60s+） |
| qwen2.5:1.5b | ✅ | 通用推理 |
| nomic-embed-text:latest | ✅ | embeddings |

## Ollama 远程库 Vision 模型（api.ollama.com 查询）

实际返回：
- `gemma3:27b` ✅
- `gemma3:12b` ✅
- `gemma3:4b` ✅
- `qwen3-vl:235b-instruct` ✅

**未找到**：`blaifa/InternVL3_5:4B`（Mac bug + 不在库中）

## screen_watcher 链路状态

| 组件 | PID/状态 | 最后活动 |
|------|---------|---------|
| screen_watcher.py | PID 61102 | 5月30日 07:46 current.png (2.3MB) |
| screen_trigger_handler.py | PID 17499 | 5月30日 07:45 dry-run 触发 |
| AUTO-EXEC-DRY 日志 | 114条 | 持续增长 |

**结论**：链路完整，无需修复。