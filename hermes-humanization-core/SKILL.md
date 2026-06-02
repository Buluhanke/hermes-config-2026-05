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

### capture_region() 参数被忽略（2026-05-29 已修复）

`capture_region(x, y, w, h)` 声明接受四个区域参数，但内部始终用 `sct.grab(sct.monitors[1])` 截全屏，x/y/w/h 完全无用。2026-05-29 修复。

**修复**：
```python
# ❌ 之前
sct.img_to_png(sct.grab(sct.monitors[1]), output=output_path)

# ✅ 修复后
region = {"left": x, "top": y, "width": w, "height": h}
sct.img_to_png(sct.grab(region), output=output_path)
```

### Smol2Operator 归一化坐标关键洞察

Smol2Operator（HuggingFace, 2025-09）实验证明：归一化坐标（0-1 范围）比像素坐标在 ScreenSpot-v2 上高 **20x**（41% vs 4%）。

当前 `find_element_by_vision()` prompt 要求模型返回像素坐标（`x: 整数, y: 整数`），而 smolvlm2-agentic-gui 训练数据使用归一化坐标。**推荐改用归一化坐标 prompt**以匹配模型训练分布。

### 已验证的坑点

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
```

**CloakBrowser 真人化（2026-05-28验证，2026-05-29更新）**

**关键发现1：CloakBrowser launch参数是`humanize`，不是`human`**：
```python
# ❌ 错误
browser = cloakbrowser.launch(human=True)  # TypeError!

# ✅ 正确
browser = cloakbrowser.launch(humanize=True, human_preset="default")
```

**关键发现2：CDP Chrome 9333的实际情况**

端口9333的Chrome进程（PID 43132）实际就是用户日常Chrome的进程，但用了一个独立的user-data-dir：
```
/Applications/Google Chrome.app/... --user-data-dir=/Users/aimac/.hermes/chrome-debug --remote-debugging-port=9333
```

这意味着：
- browser工具控制的是用户Chrome进程本身，不是独立进程
- 但profile是隔离的（`.hermes/chrome-debug` vs `~/Library/Application Support/Google/Chrome/Default`）
- **用户已登录的cookies在Default profile，不在chrome-debug profile**
- 因此browser工具访问的网站都显示未登录（即便用户Chrome已登录）

**解决方案：见上方"关键坑2（2026-05-31）"**

**可用方案对比**：

| 方案 | 优点 | 缺点 |
|------|------|------|
| CDP 9333 + cloakbrowser.patch_page | 真人化注入到已有CDP Chrome | 无用户1688登录态 |
| cloakbrowser.launch() 新浏览器 | 全新干净隐身浏览器 | 无登录态，要重新登录 |
| 连接用户Chrome调试端口 | 可操作用户已登录会话 | 需要用户手动启动Chrome加参数 |
| computer_use控制用户屏幕 | 能看到用户界面 | 窗口bounds为0，窗口不可见 |

**2026-05-28 新发现：用户Chrome调试端口故障排查**

Chrome进程启动但端口不监听的根因：
- Chrome进程`ps`能看到，但`lsof`没有监听端口 → Chrome没正常启动调试服务
- 症状：进程存在（PID XXX），但`curl localhost:9222`返回502或超时
- 最常见原因：Chrome实例冲突（另一个Chrome已在运行，占用了相同user-data-dir）

**解决步骤**：
1. Activity Monitor强制退出所有Chrome进程（包括Helper）
2. 运行带独立user-data-dir的命令：
```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```
3. 验证：`curl http://localhost:9222/json`应有JSON响应

**2026-05-28 用户纠正：不要问，直接做**

用户明确说："你完全可以按你的思路两个或者多个方向去试试"。这条原则写入工作流：
- 多个方向并行尝试时，不问用户确认，直接同时执行
- 只在有明确选择且影响不可逆时，才问用户

**关键坑2（2026-05-31）：browser工具用Hermes专属Chrome，与用户Chrome隔离**

```
用户Chrome（日常）: ~/Library/Application Support/Google/Chrome/Default → 已登录所有AI网站
Hermes Chrome: /Users/aimac/.hermes/chrome-debug (PID 43132) → browser工具控制，无登录态
```

**browser工具(MCP chrome_bridge)连接的是Hermes Chrome，不是用户Chrome。**
- 症状：browser_navigate打开gemini.com显示"未登录"，但用户日常Chrome已登录
- 确认方法：`ps aux | grep "user-data-dir"` 看Chrome进程的实际data-dir路径

**解决方案（按优先级）：**

A. **在Hermes Chrome重新登录一次**（最简单）
   - 登录后cookies保存，以后直接用
   - browser工具直接操作，无需额外配置

B. **用AppleScript操作用户Chrome**（绕过调试端口限制）
   ```bash
   osascript -e 'tell application "Google Chrome" to open location "https://gemini.google.com/app"'
   ```
   - AppleScript可以直接操作用户Chrome，不需要调试端口
   - 但速度慢、需要窗口可见，适合偶发操作

C. **把你日常Chrome的Cookies复制到Hermes Chrome profile**
   - 找到两个Chrome的Cookie文件路径
   - 用SQLite导出导入Cookie
   - 复杂度高，不推荐

**推荐：方案A（简单直接）+ 方案B（备用）**

**已知坑：computer_use无法看到Chrome窗口**

`computer_use`控制台Chrome时，所有AX元素bounds为0，窗口标题显示`about:blank`。
原因：Hermes专用Chrome（9333端口）与用户Chrome是独立进程。
解决：用户Chrome开启调试端口后，用Playwright CDP连接，不走computer_use。

**推荐1688自动化路径（2026-05-28验证成功）**：
**推荐1688自动化路径（2026-05-28验证成功）**：

1. 用户Chrome开启调试端口（加 `--remote-allow-origins=*`）：
   ```
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --user-data-dir=/tmp/chrome-debug \
     --remote-allow-origins=*
   ```
2. Python用`websocket`库连接CDP
3. 用`Target.createTarget`在browser endpoint创建新tab
4. 从`/json`获取新tab的websocket URL
5. 向tab发`Page.navigate`命令

**完整代码模板见 `references/1688-cdp-automation.md`**

**2026-06-01 新增：操作用户真实Chrome（已验证）**

browser工具控制的是Hermes专属Chrome（无用户登录态）。要操作用户已登录的AI网站（豆包/ChatGLM等），需要直连用户Chrome：

```bash
# 杀掉现有Chrome，用用户真实profile启动debug端口
pkill -9 "Google Chrome"
sleep 2
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Profile 1"
```

然后用Python CDP WebSocket连接 `ws://127.0.0.1:9333/devtools/page/<id>`，用 `Runtime.evaluate` 执行JS操作页面。

**完整操作流程见 `references/user-chrome-cdp-control.md`**

**关键坑**：
- Chrome必须加`--remote-allow-origins=*`，否则WebSocket handshake返回403
- 用browser CDP endpoint发`Target.createTarget`，不是tab endpoint
- 验证码拦截：新Chrome没有1688登录态，首次需用户手动登录一次
- `lsof`看不到端口但`curl`返回502 = Chrome进程存在但调试服务异常 → 先kill所有Chrome进程再重启

**已升级到cloakbrowser 0.3.31**（之前是0.3.30）。PyPI验证：GitHub 21,907 stars，MIT协议。

**HumanConfig 关键参数**：typing_delay（打字延迟ms）、mistype_chance（误触概率）、mouse_min_steps/mouse_max_steps（鼠标曲线路径步数）、idle_between_actions（操作间停顿）、idle_between_duration（停顿秒数范围）

**2026-06-01 新增：AI聊天网站对话获取知识（已验证失败但路径明确）**
**2026-06-02 重要发现：Shadow DOM 隔离比预期更深，浏览器读取 AI 对话此路不通**

实测结果：
- DeepSeek：输入文字✅、发送✅、Accessibility Tree 285节点✅，但 AI 回复 0 节点
- 豆包/Grok：同样 Shadow DOM 隔离，读不到任何回复内容

根因：现代 AI 聊天网站（DeepSeek/豆包/Grok/ChatGPT 等）使用 custom elements + closed shadowRoot + 虚拟化列表，DOM 遍历和 AX Tree 都无法穿透。

**正确结论**：不要通过浏览器读取 AI 对话内容，直接调 AI 厂商 API。
- ✅ 可用：AX Tree 读页面结构、填输入框、点按钮、读历史对话列表
- ❌ 不可用：读 AI 实时回复（Shadow DOM 隔离）

**2026-06-01 新增：AI聊天网站对话获取知识（已验证失败但路径明确）**
**症状**：豆包/ChatGLM 在 Playwright 无头浏览器中打开后：
- 页面正常加载，有输入框
- 发送消息后 AI 不回复（限流或风控拦截）
- 豆包弹出图片验证码；ChatGLM 无响应

**根因**：这些网站检测 headless Playwright 模式，会静默拦截请求。

**已验证可行的替代方案**：

| 方案 | 工具 | 状态 |
|------|------|------|
| Bing搜索 | Python urllib + requests | ✅ 可用 |
| browser_console 读动态内容 | browser_console | ✅ 可用（比snapshot更可靠） |
| 1688 CDP | Python websocket 直连 | ✅ 之前已验证 |

**browser_console 优于 browser_snapshot 的场景**：
```javascript
// browser_snapshot 只能看到静态DOM结构
// browser_console 可以读取动态渲染内容
document.querySelector('[class*="message"], .conversation-item')?.innerText
document.body.innerText.substring(0, 8000)
```

**用户纠正（2026-06-01）：不要走后台浏览器，走用户打开的浏览器**

用户明确指出：Hermes应该直接操作用户日常Chrome，而不是Playwright临时实例。
**操作用户Chrome的两种方式**：
- AppleScript：快速发指令（`open location`），但读不到DOM
- Chrome Debug Port + CDP WebSocket：完整控制（读DOM、执行JS、截图）
详见 `references/user-chrome-cdp-control.md`

详见 `references/user-chrome-cdp-control.md`

**SearXNG MCP 不是独立服务**：
- `npx -y searxng-mcp` 需要 serverUrl 参数，不是直接可运行的服务
- 需要配置一个正在运行的 SearXNG 实例 URL
- web_search 返回 502 时，用 Python urllib 直连 Bing 作为降级方案

**推荐知识获取路径**：
1. 首选：`execute_code` + Python urllib → Bing 搜索 → 提取 snippet
2. 次选：browser_navigate → browser_console 读 innerText（需要AI网站有登录态）
3. 备选：1688 CDP 提取商品详情（已验证）

### 真人化六维度进度（2026-06-02 更新）

| 方向 | 优先级 | 状态 | 说明 |
|------|--------|------|------|
| 一、鼠标轨迹 | ⭐⭐⭐⭐⭐ | ✅**完全体** | cos-S 贝塞尔 (二阶导数连续) + 过冲 + 渐进减抖 + 末端悬停，详见 `references/human-biometrics-algorithms.md` |
| 二、反浏览器检测 | ⭐⭐⭐⭐ | ✅已完成 | CloakBrowser已装已验证，CDP 9222端口全流程跑通 |
| 三、算子拟人化 | ⭐⭐⭐ | ✅**完全体** | 生物识别打字：cos-S 速度 + 高斯+爆发+笔误+手交替+思维停顿 |
| 四、全屏感知 | ⭐⭐⭐⭐ | ✅已完成 | CDP WebSocket截图+Runtime.evaluate提取，1688详情页数据完整拿到 |
| 五、移动端 | ⭐⭐ | ❌未完成 | 零进展 |
| 六、语音真人化 | ⭐⭐⭐ | ⚠️部分 | Moss-TTS音色已配，情感/停顿未搞 |

**2026-06-02 重大升级：完全体真人化驱动**
- 独立模块：`~/.hermes/scripts/hermes_human_biometrics.py` (24KB)
- 鼠标：cos-S 三次贝塞尔 + 双控制点偏移 + 过冲修正 + 渐进减抖
- 键盘：8 维生物特征（高斯延迟+爆发模式+思维停顿+笔误纠正+手交替+Shift时序+特殊键+标点停顿）
- 算法详解：`references/human-biometrics-algorithms.md`
- reactor_v3 act() 已切换到完全体，旧版简化函数保留作 fallback

**2026-05-29 重大突破：1688采购全流程跑通**
- 搜索"纸箱" → 34页商品列表，标题/价格/供应商/起订量全部提取
- 点进商品详情页 → 提取：标题、价格¥0.1、起订量100个、已售8.5万+个
- 关键技术：CDP WebSocket直连（端口9222）+ `Runtime.evaluate` JS提取动态内容
- 核心教训：问"要不要做"是错的——明确该做的事直接做，只在有真正选择时才问

### browser-use 集成参考（2026-06-01）

browser-use（第三方浏览器自动化框架）与 Google Generative AI (Gemini) 集成记录见 `references/browser-use-gemini-integration.md`。

核心发现：browser-use 0.12.8 使用自定义消息类型和 structured output 模式，与 LangChain 的 Gemini 集成不兼容（导航可用，连续对话不可用）。

**下一步自己推进**（不等用户问）：
