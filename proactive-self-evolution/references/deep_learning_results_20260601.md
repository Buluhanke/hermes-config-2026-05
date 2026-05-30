# 深度学习结果归档 (2026-06-01凌晨)

## 任务：Browser-Use + Playwright + 本地VLM 连调

### 完成情况

**✅ qwen3-vl:latest (6.1GB) 下载完成**
```
ollama pull qwen3-vl  # 模型名是 qwen3-vl 不是 qwen3-vl:7b
```

**✅ Browser-Use 0.12.9 兼容性修复（5处patch）**

| 文件 | 修复内容 |
|------|----------|
| `browser_use/agent/service.py:235` | `llm.provider` → `getattr(llm, 'provider', None)` |
| `browser_use/agent/service.py:1603` | `self.judge_llm.provider` → `getattr(...)` |
| `browser_use/agent/service.py:2045` | log中provider字段安全访问 |
| `browser_use/agent/service.py:2211` | telemetry中model_provider安全访问 |
| `browser_use/agent/cloud_events.py:217` | `model_name` → fallback到`model` |

**✅ python-socks 安装完成**
```bash
uv pip install python-socks --python ~/.hermes/hermes-agent/.venv/bin/python
```

**✅ Chrome调试端口9333启动**
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/.hermes/chrome-debug" &
```

### 模型能力测试结果

| 模型 | 导航 | 内容提取 | 结论 |
|------|------|----------|------|
| qwen2.5:1.5b | ✅ 成功 | ❌ 失败 | 太小，推理循环不收敛 |
| qwen3-vl:2b | ✅ 成功 | ❌ 失败 | 同上 |
| qwen3-vl:latest (6.1GB) | ✅ 成功 | ❌ 失败 | 仍不够，6步内全部失败 |

### 核心问题

**Browser-Use 框架本身已修复可用**，但：
1. 连接已有Chrome的CDP需要 `python-socks`（已装 ✅）
2. 需要更大参数的本地VLM才能稳定驱动推理循环（当前最大7b仍不够）
3. Stagehand 官方版需要 Browserbase 付费账号，本地 MCP 方案需单独配置

### 结论

**Browser-Use 修复完成，模型能力是当前瓶颈。**
- 下一步：等 qwen3-vl:14b+ 模型下载完成后再测试完整闭环
- 或换用云端GPT-4o作为临时方案

### 相关脚本

- `~/.hermes/scripts/test_browser_use_cdp.py` — Browser-Use + CDP测试脚本
- `~/.hermes/scripts/check_browser_use.py` — 检查Browser-Use配置