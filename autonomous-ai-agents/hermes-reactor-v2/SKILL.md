---
name: hermes-reactor-v2
description: Hermes 自主执行反应堆 v3 — 短期记忆 + SOP 编排 + 5种SelfHealing + LLM Think + data_buffer天眼流。Sense → Think → Act 死循环跑 Chrome 标签页, 支持 AI 自动对话 / 1688 sourcing / 自定义任务链。
version: 3.0
category: autonomous-ai-agents
keywords: [reactor, autonomy, memory, sop, planning, self-healing, sense-think-act, cdp, llm-think, data-buffer]
---

## Pitfall 19: DeepSeek React textarea 值被清空（已解决，不需要 Playwright）

### 现象（旧认知，已过时）
`ta.value = '...'` 能写入，`btns[8].click()` 能执行，但 AI 永远不回复——React 内部状态未更新。

### ✅ 真实解法：WebSocket 逐字输入（已验证 4 次，2026-06-02）

**核心工具**：`browser_cdp` 工具走 WebSocket，**不是** `cdp_type.py`（后者用 curl HTTP，走不通）

**完整链路**：
```python
# 1. WebSocket 连接 tab
async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws:
    # 2. 聚焦 textarea
    await cdp.send("Runtime.evaluate", {
        "expression": "document.querySelector('textarea').focus()",
        "returnByValue": True
    })
    # 3. 逐字输入（每字符 keyDown→char→keyUp，间隔 0.05s）
    for ch in text:
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "keyDown", "key": ch, "text": ""
        })
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "char", "text": ch
        })
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "keyUp", "key": ch
        })
        await asyncio.sleep(0.05)
    # 4. Enter 发送
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "Enter", "code": "Enter",
        "text": "\r", "keyCode": 13, "location": 0
    })
```

**验证结果**（2026-06-02 实测 4 次）：
- "1+1等于几" → ✅ 21字正确回复
- "什么是AI" → ✅ 完整长回答
- "用三个词形容Hermes" → ✅ 完整
- "解释量子计算" → ✅ 完整

**关键**：`browser_cdp` 工具调 CDP 走 WebSocket，**不是** `terminal + curl`（后者调 HTTP 走不通）

### ⚠️ cdp_type.py 是错误方案
`cdp_type.py` 用 `subprocess.run(["curl", "-s", "-X", "POST", ...])` 调 CDP HTTP 接口，
`Input.dispatchKeyEvent` 等 WebSocket 专属命令返回 `Unknown command`。**废弃**。

---

## Pitfall 20: CDP HTTP 路径不支持 WebSocket 专属命令

### 现象
`curl -X POST http://127.0.0.1:9333/json/{tab_id}/Input.dispatchKeyEvent` 返回 `Unknown command`。

### 根因
`Input.dispatchKeyEvent`、`Runtime.evaluate` 等命令只能走 WebSocket（CDP 协议层），HTTP POST 不支持这些命令。

### 修复
- 只能用 `browser_cdp` 工具走 WebSocket，不能用 `terminal + curl` 替代
- `execute_code` 需要每次授权，不适合高频循环
- **结论**：`browser_cdp` 是唯一无需授权且能跑通 WebSocket 命令的工具

---

## Pitfall 21: execute_code 授权 vs browser_cdp 工具调用（用户误感知"每次都要授权"）

### 现象
用户感觉"每次都要授权"，实际上是 `execute_code` 的审批机制在触发。

### 澄清
| 工具 | 是否需要授权 |
|------|------------|
| `browser_cdp` | ❌ 不需要（工具调用） |
| `terminal` | ❌ 不需要（shell） |
| `execute_code` | ✅ 每次需要（Python 执行） |
| `mcp_chrome_*` | ❌ 不需要（MCP 工具） |

### 结论
高频 CDP 操作（逐字输入循环）**必须用 `browser_cdp` 工具**，不能用 `execute_code` 或 `terminal + curl` 替代。

## 是什么

将 Hermes 升级为**自主执行体**，具备:
- **短期记忆** (HermesMemory): Context Buffer + 状态锁 + 行动历史
- **天眼流存储** (data_buffer): 每周期状态快照，写入文件用于诊断
- **SOP 任务编排** (HermesTaskCard): 多阶段计划自动对齐与推进
- **5种异常 SelfHealing**: PAGE_STUCK / CAPTCHA / LOGIN_EXPIRED / NETWORK_ERROR / BLANK_PAGE
- **RECREATE_TAB 自愈**: 会话死亡时自动重建 tab
- **LLM Think 层**: MiniMax 驱动 SOP 决策（429 时降级规则引擎）
- **持久化**: 记忆写入 `/tmp/hermes_memory_<tab>.json`，网关重启可恢复

## 何时用

- **24h 挂机跑 AI 站** (DeepSeek / 豆包 / Gemini / ChatGPT) 自动对话
- **1688 / 拼多多采购工作流**（搜 → 选 → 联系 → 记录）
- **多步骤业务自动化**（任何有"输入→等回复→处理"模式的场景）

### ⚠️ 输入方案优先级（2026-06-02 更新）

| 方案 | 工具 | 适用网站 | 优点 | 缺点 |
|------|------|---------|------|------|
| **✅ CDP WebSocket 逐字** | `browser_cdp` 工具 | DeepSeek ✅ ChatGLM ✅ | 触发 React onChange，4次验证稳定，不占额外内存 | 每字符单独调用，速度略慢 |
| **❌ cdp_type.py (curl HTTP)** | `terminal + curl` | 全部失效 | — | `Input.dispatchKeyEvent` 返回 `Unknown command`，废弃 |
| ⚠️ Playwright | `page.press_sequentially()` | DeepSeek 备用 | 触发真实 onChange | 多占 200-300MB，execute_code 需授权 |

**结论**：`browser_cdp` 工具走 WebSocket 是 DeepSeek 输入的正确答案，不需要 Playwright。

## 何时不用

- 一次性的简单点击任务（用 vision_click 即可）
- 需要 OCR 视觉识别的复杂图像（反应堆走 AX/JS 路线，不读图）

## 核心架构

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Sense 感知层 │──▶│ Think 认知层 │──▶│  Act 执行层   │
│ (CDP evaluate)│   │ (LLM/规则)   │   │ (CDP input)  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
   stateHash          HermesMemory       log_action
   bodyLen            current_stage      RECREATE_TAB
   isLoading          action_lock        set_stage
        │                  │
        └─────────▶  data_buffer (天眼流快照)
```

## 内存模型 (HermesMemory)

```python
{
    "last_action": "ENTER_SEND",       # 上一轮动作
    "action_timestamp": 1780397615.0,  # 时间戳
    "current_stage": "WAITING",        # INIT → READY → WAITING → COMPLETED
    "retry_count": 0,
    "stuck_cycles": 0,                 # 连续无变化周期
    "last_state_hash": "1|815|45|0|0",
    "last_body_len": 815,
    "data_buffer": [...],               # 天眼流（最近20周期快照）
    "plan": {...},                     # 当前SOP
    "current_step": 0,
    "step_results": [],
    "history": [...]                   # 最近20条行动
}
```

## 状态机 4 阶段

| 阶段 | 触发条件 | 允许动作 | 下一阶段 |
|------|----------|----------|----------|
| INIT | 启动 | TYPE_MESSAGE | → READY |
| READY | 输入完成 | CLICK_SEND / ENTER | → WAITING |
| WAITING | 已提交 | WAIT（等 AI 输出）| → COMPLETED |
| COMPLETED | body > 200 | DONE | 结束 |

## SelfHealing 5种异常

| 异常 | 检测条件 | 处置 |
|------|----------|------|
| PAGE_STUCK | 18周期 + loading=False + body无增长 + last_body_len>0 | RECREATE_TAB |
| CAPTCHA | 连续3周期检测到验证码元素 | 报警+退出 |
| LOGIN_EXPIRED | 检测到登录框/未登录状态 | 报警+退出 |
| NETWORK_ERROR | 连续3周期 WS 连接失败 | 重连 |
| BLANK_PAGE | 连续3周期 body<50 | 刷新 |

## 实战验证 (DeepSeek, 90秒测试)

```
周期1:  INIT → TYPE (14字符) → READY
周期2:  READY → ENTER_SEND 兜底 → WAITING
周期3:  WAITING body 938→999 增长 → COMPLETED
周期4-27: SOP 5步自动推进，每步检测完成→NEXT_STEP
总耗时: 69.5秒, 27周期, 5/5步骤完成, 0次误判
```

**核心证据**:
- ✅ 状态锁防止重复触发（action_lock cooldown 生效）
- ✅ 5阶段 SOP 自动流转
- ✅ body 增长信号正确检测 AI 输出
- ✅ Enter 兜底代替缺失按钮
- ✅ RECREATE_TAB 零触发（DeepSeek 会话正常）

## 命令行用法

```bash
# 单站点自动对话（默认 auto_chat SOP，90秒超时）
python3 hermes_reactor_v3.py deepseek 90 "用三个词回答：今天感觉怎么样"

# 带初始问题
python3 hermes_reactor_v3.py deepseek 30 "用一句话说说你是什么模型"

# 指定 SOP
python3 hermes_reactor_v3.py deepseek 120 --sop custom_plan.json

# 诊断按钮误识别
python3 scripts/diagnose_button_misidentification.py deepseek
```

## 24h 挂机配方

```bash
# crontab 每 5 分钟拉起一次（反应堆自带超时）
*/5 * * * * python3 /Users/aimac/.hermes/scripts/hermes_reactor_v3.py deepseek 240 "请给我一个创业点子" >> /tmp/hermes_deepseek.log 2>&1

# 多站点轮询
*/10 * * * * python3 /Users/aimac/.hermes/scripts/hermes_reactor_v3.py doubao 200 "今天有什么AI新闻" >> /tmp/hermes_doubao.log 2>&1
*/15 * * * * python3 /Users/aimac/.hermes/scripts/hermes_reactor_v3.py gemini 180 "推荐一个开源项目" >> /tmp/hermes_gemini.log 2>&1
```

## 关联文件

- `/Users/aimac/.hermes/scripts/hermes_reactor_v3.py` — **生产版本**（714行），包含 LLM Think + 5种SelfHealing + data_buffer天眼流
- `/Users/aimac/.hermes/scripts/hermes_reactor_v2.py` — 验证基线（471行），90秒测试全链路通过
- `/Users/aimac/.hermes/scripts/chrome_cdp.py` — CDP 底层工具
- `/tmp/hermes_memory_<tab>.json` — 持久化记忆

## Act 层 — 真人化驱动（完全体：贝塞尔 cos-S + 生物识别）

Act 层 TYPE / SEND / CLICK 动作现已升级到**完全体真人化**。底层从 reactor 内部简化版切到独立模块 `hermes_human_biometrics.py`：

**鼠标端**（贝塞尔 cos-S 物理曲线 + 过冲修正 + 渐进减抖）：
- 三次贝塞尔曲线 + 双控制点侧向偏移
- S 型速度曲线 `t' = (1 - cos(t·π)) / 2`（二阶导数连续，无拐点冲击）
- 18% 概率过冲 + 8 步修正回拉（真人冲过头）
- 末端悬停 3 步 + 18ms 延迟
- 亚像素抖动 **越接近目标越小**（`shake_reduce = 1.0 - progress`，神经集中"对准"）
- 距离自适应步数 28-55
- 按下持续 60-150ms，悬停犹豫 30-90ms

**键盘端**（生物识别打字律动）：
- 高斯分布键间延迟 142±38ms
- 3-7 字符爆发-停顿模式
- 4% 概率思维停顿 600-1400ms
- 0.6% 笔误率 + 退格纠正
- 双手交替延迟（同手 +20ms, 异手 -10ms）
- Shift/Backspace 真实时序

**接入模式**（reactor_v3.py 中的 `act()`）：
```python
try:
    from hermes_human_biometrics import human_click, human_type
    HUMAN_BIOMETRICS_OK = True
except ImportError:
    HUMAN_BIOMETRICS_OK = False

# TYPE: cos-S曲线滑入 + 生物识别打字
if HUMAN_BIOMETRICS_OK:
    cx, cy = self._mouse_pos
    self._mouse_pos = await human_click(self.cdp, self.tab["id"], inp_x, inp_y, cx, cy)
    await human_type(self.cdp, self.tab["id"], text)
else:
    # 降级到 reactor 内部简化版
    self._mouse_pos = await human_mouse_click(self.cdp, inp_x, inp_y, current_mouse_pos=self._mouse_pos)
    await human_type_text(self.cdp, text)
```

**CDP 客户端 session_id 扩展**：`Input.dispatchMouseEvent` / `Input.dispatchKeyEvent` 必须带 `sessionId: <tab_id>` 才能命中具体 tab：
```python
class CDP:
    async def send(self, method, params=None, session_id=None):
        payload = {"id": CDP.msg_id, "method": method, "params": params or {}}
        if session_id:
            payload["sessionId"] = session_id
        await ws.send(json.dumps(payload))
```

**风控效果**：Mouse Tracking 捕获贝塞尔曲线点阵（cos-S 速度）+ Keyboard Timing 捕获非匀速生物节律（高斯 + 爆发 + 笔误），双重真人化特征。
**算法详解**：`~/.hermes/skills/hermes-humanization-core/references/human-biometrics-algorithms.md`

## Support 文件

- `references/decision-design.md` — 4 个核心设计决策的"为什么"(body_growing 替代 stopBtn / 18 周期阈值 / 状态锁冷却 / Enter 兜底)
- `references/pitfalls.md` — 所有踩过的坑（含 DeepSeek React 清空值 / CDP HTTP 命令失效 / execute_code 授权误判）
- `templates/auto_chat_sop.json` — AI 自动对话 SOP 模板（8阶段，带 loops 和 self_heal 配置）
- `templates/1688_sop.json` — 1688 sourcing SOP 模板（5阶段：导航→搜索→选品→联系客服→记录）
- `scripts/diagnose_button_misidentification.py` — 按钮误识别静态探针
- `scripts/auto_web_chat.py` — **Playwright 免授权脚本**，支持 ChatGLM/DeepSeek/豆包，替代 CDP 逐字输入方案

## Pitfalls 速查 — 详见 references/pitfalls.md

1. **"开启新对话"误识别为发送按钮** — 严格 `t === '发送'`，按宽度排序选最小
2. **Shadow DOM 屏蔽 stopBtn** — 改用 bodyLen 增长信号
3. **DeepSeek 慢思考 30-60s** — 阈值 18 周期（36s）
4. **F-string 反斜杠** — JS 模板用 `+` 拼接，不用 f-string
5. **CDP 消息格式** — 无 `jsonrpc` 字段，只有 `id` + `method` + `params`
6. **Input.dispatchKeyEvent text="" 双计数** — keyDown 不带 text
7. **body 阈值 800 误判短回复** — 降到 200
8. **RECREATE_TAB 直接关闭 ws** — 用活 tab 的 ws 发 Page.navigate
9. **PAGE_STUCK 在 AI 输出中被误触发** — 必须满足 `last_body_len > 0`（之前有增长过）
15. **M3 key 授权范围 ≠ M2.7** — 逐模型验证
16. **DeepSeek React 输入状态陷阱（已解决）**：用 `browser_cdp` 工具走 WebSocket + `hardcore_type` 逐字输入（keyDown→char→keyUp），4次验证稳定。不需要 Playwright。

### 🔴 Critical: hermes config 交互界面不持久化 API Key

**问题现象**：`hermes config` 交互界面填写 API Key 后，config show 显示 "AICODEE_API_KEY"（变量名引用），但：
- `.env` 中无 `AICODEE_API_KEY=...` 行
- `auth.json` 的 `credential_pool` 中无对应条目
- `providers` 字典中无 aicodee

**根因**：`hermes config` 的 masked input 写入了 `config.yaml` 的 `api_key_env: AICODEE_API_KEY`（只是变量名），从未写入实际 key 值。

**影响**：所有引用 `AICODEE_API_KEY` 的 provider（aicodee / custom endpoint）运行时 key 为空 → 401。

**解法（按优先级）**：
```bash
# 方案A（推荐）：直接追加到 .env
echo 'AICODEE_API_KEY=*** >> ~/.hermes/.env

# 方案B：用 hermes set 存 secrets（如果支持）
hermes config set secrets.AICODEE_API_KEY sk-xxx...
**验证：填完立即 curl 测试（minimaxi.com）**
```bash
curl -s --noproxy '*' -H "Authorization: Bearer $MINIMAX_CN_API_KEY" \
  https://api.minimaxi.com/v1/models
```

**检查清单**：
- [ ] `.env` 里有 `MINIMAX_CN_API_KEY=sk-...` 这一行
- [ ] `curl` 能调通模型端点（返回模型列表，不是 401/429）
- [ ] `hermes config show` 显示的是实际 key 前缀（`sk-...`），不是变量名
16. **v2.aicodee.com 中转废弃**：已从 reactor_v3.py 和 .env 中彻底移除，base_url 切换为 `https://api.minimaxi.com/v1`
17. **hermes config 交互界面 Key 不持久化**：写的是变量名引用而非实际 key，直写 `.env` + curl 验证
18. **Python urllib 被系统代理劫持导致 SSL EOF**：macOS Clash 代理（默认 7897）会劫持所有 `https_proxy`/`http_proxy` 环境变量，Python `urllib.request.urlopen` 经代理访问 `v2.aicodee.com` 会触发 `[SSL: UNEXPECTED_EOF_WHILE_READING]`。**解法**：用 `curl --noproxy '*'` subprocess 替代 urllib，curl 会绕过系统代理直连。完整模式见 `templates/curl_no_proxy_pattern.md`（如不存在则参考 reactor_v3.py 的 `_call_via_curl`）
19. **M2.7-highspeed 等推理模型响应在 `reasoning_content` 而非 `content`**：调用后 `msg["content"]` 永远是空字符串，真实答案在 `msg["reasoning_content"]`。**解析必须 fallback**：`content = msg.get("content") or msg.get("reasoning_content") or ""`
20. **`no_proxy=*` 在 Python urllib 不生效**：必须用 curl 或在程序启动时 `os.environ.pop("https_proxy", None)` 才能真正直连。`requests` 库在 macOS 上同样有这个问题
