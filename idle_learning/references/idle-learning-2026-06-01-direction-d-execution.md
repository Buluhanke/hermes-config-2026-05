# 2026-06-01 方向D学习记录：执行层调研

## 产线健康快照

| 检查项 | 状态 |
|--------|------|
| screen_watcher | ✅ PID 8748, 1:27AM 启动 |
| Ollama | ✅ qwen3-vl:2b + qwen2.5:1.5b |
| 截图新鲜度 | ✅ current.png 04:50, 3.3MB |
| unknown 率 (06-01) | ✅ **0%** |
| AUTO-EXEC-DRY | 254条 (06-01 凌晨段) |
| 场景分布 | 100% "other" (深夜空闲) |
| 网络 | github/HN blocked, HN Firebase OK |

## 核心发现

### 1. RPA 动作利用率瓶颈

RPA 脚本 (`hermes_desktop_rpa.py`) 支持 **11 种动作**，但 `ACTION_WHITELIST` 仅用 **3 种**：

| 动作 | 命令格式 | 使用状态 |
|------|---------|---------|
| `wininfo` | `python3 rpa.py wininfo` | ✅ 活跃场景主动作 |
| `ocr` | `python3 rpa.py ocr` | ✅ 1688 场景专用 |
| `none` | — | ✅ idle 场景静默 |
| `click x,y` | `python3 rpa.py click 960,860` | ❌ 未使用 |
| `type text` | `python3 rpa.py type "text"` | ❌ 未使用 |
| `press key` | `python3 rpa.py press enter` | ❌ 未使用 |
| `scroll n` | `python3 rpa.py scroll -3` | ❌ 未使用 |
| `openurl url` | `python3 rpa.py openurl https://...` | ❌ 未使用 |
| `send msg` | `python3 rpa.py send "msg"` | ❌ 未使用 |
| `readchat` | `python3 rpa.py readchat` | ❌ 未使用 |
| `activate` | `python3 rpa.py activate` | ❌ 未使用 |
| `url` | `python3 rpa.py url` | ❌ 未使用 |

**瓶颈不是 RPA 能力不够，是 handler 没做 element-level grounding。**

### 2. 坐标映射链

- Qwen3-VL 输出归一化 [0, 999] 坐标（DeepWiki 确认）
- GitHub #1576 报告 grounding 精度 < 2%（格式错误 + 坐标范围不一致）
- P0 任务：`normalized_click(nx, ny, sw, sh)` 函数
- SafeGround 多采样校准是 DRY_RUN=False 的必要前置

### 3. arXiv 2510.04607 DMI (Declarative Model Interface)
- 策略-机制分离架构 = 验证 scene_classifier → action_executor 设计
- Microsoft Office Suite: +67% success, -43.5% steps
- 三元组 (access/state/observation) 可借鉴到 Verify 阶段

### 4. Gateway 污染修复（handler.py 清空）
- HOOK.yaml `events: []` 不足——Gateway 启动时仍会加载 handler.py
- 注入点：`from humanization_core import capture_screen, ask_vlm`
- 修复：清空 `~/.hermes/hooks/screen_watch/handler.py`（仅占位 docstring）
- 验证：`grep -c "screen_watch" ~/.hermes/logs/gateway.log` 停止增长

### 5. DRY_RUN=False 前置条件检查（自 idle_learning/Direction D）

| # | 条件 | 状态 | 
|---|------|------|
| ① 基线数据 | ✅ 254条 (06-01) |
| ② unknown 率 | ✅ 0% (06-01 按日期分片) |
| ③ 动作多样性 | ❌ 仅3种（RPA支持11种） |
| ④ 坐标映射链 | ❌ 待实现 |
| ⑤ SafeGround 置信度 | ❌ 待实现 |
| ⑥ 动作分级 | ⚠️ 基础版已有（idle→none, business→wininfo） |

## 变更
- `handler.py` — 清空（仅占位 docstring）
