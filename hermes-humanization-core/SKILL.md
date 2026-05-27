---
name: hermes-humanization-core
description: "Phase 1+2 核心：动作拟真 + 视觉感知 + 人机控制权交接。突破反爬风控，操控任意桌面软件。"
---

# hermes-humanization-core

**Phase 1+2 核心**：动作拟真（pyautogui）+ 视觉感知（VLM）+ 人机控制权（pynput）。突破反爬风控，操控任意桌面软件。

## 触发条件

- 需要操作 1688 / 微信 / 任意无 API 的桌面软件
- CDP / DOM 树无法定位的元素（动态加载、无固定结构、跨软件）
- 需要绕过反机器人检测（风控检查点）
- 需要人类临时接管再交还控制权

## 核心机制：Visual-Action-Verify 闭环

这是 Hermes 区别于普通 RPA 脚本的核心差异——每次操作都走"看→做→确认→纠错"的人类循环。

```
vlm_click("发送按钮")
  │
  ├── ① Think: 截图 → VLM 找"发送按钮"坐标
  ├── ② Act: human_click(x, y) 拟真点击
  ├── ③ Verify: 再截一张屏 → VLM 问"按钮按下去了吗？"
  └── ④ Reflect: 如果没成功，分析原因重试（最多 2 次）
```

所有 `vlm_click()` 调用都自带这个闭环。失败时会自动重试并调整策略。

## 架构概览

```
暗网层（快）：CDP 9333 / MCP Chrome → 1688 数据抓取、批量操作
显性层（拟真）：humanization_core → 前端交互、风控绕过、无 API 软件操控
调度层：根据任务类型自动判定走哪条路
```

## 核心函数

```python
from humanization_core import (
    # 动作拟真
    human_type,         # 模拟打字（错字回退 1% 概率 + 随机延迟）
    human_move,         # 贝塞尔曲线鼠标移动（动态速度：远则慢近则快）
    human_click,        # 移动 → 悬停 → 按下 → 抬起
    human_scroll,       # 分段滚轮（分 3-5 次，间隔随机）
    
    # 视觉感知
    capture_screen,     # 极速截屏（mss 库）
    ask_vlm,            # 默认 qwen2.5vl:7b，截图问答
    ask_vlm_fast,       # 备选 smolvlm2，快速低精度视觉问答
    find_element_by_vision,  # 截图 → VLM 找坐标 → 返回 (x, y)
    vlm_click,          # 主流程：截图 → VLM 找 → 拟真点击 → 截图确认 → 重试
    
    # 情绪感知
    analyze_emotion,    # 文本情绪分析（qwen3:8b）
    human_reading_time, # 文本阅读耗时估算
    send_message_with_breath,  # 分段发送，模拟"正在输入"
    
    # 人机控制权
    is_human_takeover_active,  # 检查人类是否在操作
    wait_for_human_release,    # 等待人类交还控制权
)
```

## 默认 VLM 模型

| 模型 | 函数 | 加载速度 | 准确度 | 内存占用 | 状态 |
|------|------|---------|--------|---------|------|
| smolvlm2（默认） | `ask_vlm()` | 2-5s | 中 | ~2GB | ✅ 已安装 |
| qwen2.5vl:7b（备选） | `ask_vlm_fast()` | 首次 12s，后续 1-2s | 高 | ~9GB | ❌ 未安装 |

> **2026-05-27 实测**：qwen2.5vl:7b 在当前 Ollama 中不存在。`humanization_core.py` 已将 smolvlm2 改为主模型，qwen2.5vl 降为备选。
> 首次调用 qwen2.5vl:7b 时会加载模型到内存（约 12 秒），后续调用仅 1-2 秒。

**验证当前 Ollama 已有模型**（必须先确认再引用）：
```bash
curl -s http://127.0.0.1:11434/api/tags | python3 -c "import json,sys; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"
```
当前仅有：`ahmadwaqar/smolvlm2-agentic-gui:latest`、`nomic-embed-text:latest`。
首次调用 qwen2.5vl:7b 时会加载模型到内存（约 12 秒），后续调用仅 1-2 秒。

## 典型工作流

### 场景1：视觉找元素并点击
```python
# 截图 → VLM 找到发送按钮坐标 → 贝塞尔曲线移动 → 悬停 → 点击 → 截图确认
vlm_click("发送按钮")
# 内部实现：find_element_by_vision → human_click → capture_screen → ask_vlm(确认)
```

### 场景2：人机控制权交接
```python
from humanization_core import is_human_takeover_active, wait_for_human_release

# 每次关键操作前检查
if is_human_takeover_active():
    print("用户正在操作，Hermes 暂停")
    # 等待用户操作完毕（超时 30 秒）
    wait_for_human_release()

# 执行下一步操作
human_click(x, y)
```

### 场景3：情绪感知路由
```python
emotion = analyze_emotion("又拖了！！！")
if emotion['urgency'] == '高':
    # 跳过热身，直接给结论
    print(f"[情绪={emotion['emotion']}, 紧急={emotion['urgency']}] 供应商已确认")
else:
    print("早，有个事跟您说下...")
```

### gateway venv 依赖隔离（重要！）

`humanization_core` 被 `hooks/screen_watch/handler.py` 引用时，运行在 `hermes gateway` 进程里——用的是 `~/.hermes/hermes-agent/.venv/bin/python`（venv环境），**不是系统Python**。

**症状**：`screen_watch` hook 打印 `[screen_watch] 跳过（缺少humanization_core）`，但系统Python能正常导入。

**根因**：venv 缺少 `pyautogui`、`numpy`、`mss`、`pynput`，而系统Python有。

**修复**（在 venv 里装依赖）：
```bash
cd ~/.hermes/hermes-agent
.venv/bin/python3 -m pip install pyautogui numpy mss pynput
```

**验证**（必须在 venv 环境里跑，不能只在系统Python验证）：
```bash
cd ~/.hermes/hermes-agent
.venv/bin/python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/hermes-humanization-core'))
from humanization_core import capture_screen, ask_vlm
print('ok')
"
# 预期输出：[humanization] 人机控制权监听已启动
#           ok
```

## 已知局限

- **Qwen2.5-VL 7B 在 M4 24GB 上需要 `num_ctx=4096`**（默认 128K 会溢出）
  - 已通过代码 `options={"num_ctx": 4096}` 硬编码
  - 不支持 `flash_attn=True`（Ollama 的 qwen2.5vl 实现有兼容问题）
- **pynput 需要 macOS 辅助功能权限**：系统设置 → 隐私与安全性 → 辅助功能 → 勾选终端/Python
- **视觉找坐标成功率依赖屏幕分辨率稳定性**：分辨率变化后 VLM 需要重新适应

## ⚠️ 已验证的坑点

### Qwen2.5-VL 输出 JSON 格式多样

Qwen2.5-VL 可能输出三种格式的 JSON，代码中已兼容全部：

```python
# 格式1：纯对象
{"x": 100, "y": 200}

# 格式2：代码块包裹
```json
{"x": 100, "y": 200}
```

# 格式3：数组包裹
[{"x": 100, "y": 200}]
```

解析逻辑（已写入 `find_element_by_vision`）：
```python
clean = result.strip()
clean = clean.replace("```json", "").replace("```", "").strip()
clean = clean.replace("'", '"')  # 单引号→双引号
parsed = json.loads(clean)
if isinstance(parsed, list):
    parsed = parsed[0]
```

### Qwen3 返回单引号 JSON → 情绪分析全返回默认值

`analyze_emotion()` 依赖 Qwen3:8b 返回 JSON。Qwen3 用单引号（`{'emotion': '急躁', 'urgency': '中'}`），`json.loads()` 只认双引号。

**症状**：所有情绪分析都是 `{'emotion': '平静', 'urgency': '中'}`——走了 fallback。

**修复**（已写入 `analyze_emotion`）：
```python
json_str = json_str.replace("'", '"')
result = json.loads(json_str)
```

### ChromaDB query() vs get() 返回格式不一致

`recall_supplier` 同时用 `collection.query()`（相似度搜索）和 `collection.get()`（精确匹配），两者返回的 `documents` 格式不同：

- `query()` → 嵌套 `[["doc1", "doc2"]]`
- `get()` → 扁平 `["doc1", "doc2"]`

**症状**：`json.loads()` 收到 list 报错 `TypeError: the JSON object must be str, bytes or bytearray, not list`

**修复**（已写入 `memory_hpc.py`）：
```python
docs = results["documents"]
if docs and isinstance(docs[0], list):
    docs = docs[0]
```

### vision_agent 跨 skill 引用路径

`hermes-vision-agent/vision_agent.py` 依赖 `hermes-humanization-core/humanization_core.py`。两个 skill 在不同目录。

**症状**：`ModuleNotFoundError: No module named 'humanization_core'`

**修复**（已写入 `vision_agent.py`）：
```python
_humanization_dir = os.path.join(os.path.dirname(__file__), '..', 'hermes-humanization-core')
sys.path.insert(0, os.path.abspath(_humanization_dir))
```

**约束**：两个 skill 必须在 `~/.hermes/skills/` 下的并列目录。

### Ollama 请求在 terminal 环境被代理拦截

terminal 工具继承环境变量 HTTP_PROXY，导致 localhost:11434 请求失败但**不抛异常**。

**症状**：所有 VLM/情绪分析请求静默返回默认值。

**解法**：
1. 用 `execute_code` 替代 `terminal` 做 Ollama 调试
2. 代码中已通过 `requests.post(OLLAMA_URL, ...)` 的默认行为保障（不走 proxy 反而更快）

### VLM模型默认值与Ollama实际不匹配（2026-05-27实测）

`humanization_core.py` 默认使用 `qwen2.5vl:7b`，但此模型在当前 Ollama 环境中不存在。所有 `ask_vlm()` 调用会超时失败，screen_watch hook 的视觉分析无法工作。

**症状**：`[VLM错误] model 'qwen2.5vl:7b' not found` 或超时（90秒）

**修复（已执行）**：修改 `~/.hermes/hermes-humanization-core/humanization_core.py` 第142-143行：
```python
VLM_MODEL_DEFAULT = "ahmadwaqar/smolvlm2-agentic-gui:latest"  # smolvlm2升为主模型
VLM_MODEL_FALLBACK = "qwen2.5vl:7b"  # qwen2.5vl降为备选
```

**验证**：
```bash
cd ~/.hermes/hermes-agent && .venv/bin/python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/hermes-humanization-core'))
from humanization_core import ask_vlm
print('ok')  # 不报错即导入成功
"
```

### mss 库 API 版本敏感

`mss` 在 10.0 版本有重大 API 变化：

```python
# ❌ 旧版（mss < 10.0）
sct = mss.mss()
sct.shot(output=path, monitor=1)

# ✅ 新版（mss >= 10.0）
sct = mss.MSS()
sct.shot(output=path, mon=1)
```

### HuggingFace 被墙（国内网络）

faster-whisper 首次加载时从 huggingface.co 下载模型，国内网络被 GFW 阻断。

**修复**（已写入 `voice_module.py`）：
```python
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
```

### gateway 重启时 SIGTERM 可能不生效

杀死旧 gateway 进程时，普通 `kill`（SIGTERM）可能不响应，要用 `kill -9`。

**症状**：`kill <pid>` 后 `ps -p <pid>` 仍然显示进程存在，导致启动新 gateway 时报"Telegram bot token already in use"。

**解法**：
```bash
kill -9 <pid>  # 不是 kill <pid>
sleep 2
ps -p <pid> && echo "still running" || echo "killed"
```

## 验证步骤

```bash
cd ~/.hermes/skills/hermes-humanization-core
python3 humanization_core.py
# 预期：
# [humanization] 人机控制权监听已启动
# 屏幕尺寸: Size(width=1920, height=1080)
# 情绪分析... => 返回不同情绪（不再全是"平静"）
```
