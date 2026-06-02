---
name: hermes-reactor-v2
description: Hermes 自主执行反应堆 v3 — 短期记忆 + SOP 编排 + 5种SelfHealing + LLM Think + data_buffer天眼流。Sense → Think → Act 死循环跑 Chrome 标签页, 支持 AI 自动对话 / 1688 sourcing / 自定义任务链。
version: 3.0
category: autonomous-ai-agents
keywords: [reactor, autonomy, memory, sop, planning, self-healing, sense-think-act, cdp, llm-think, data-buffer]
---

# Hermes Reactor v3 — 自主执行体（生产级）

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

- 24h 挂机跑 AI 站 (DeepSeek / 豆包 / Gemini / ChatGPT) 自动对话
- 1688 / 拼多多采购工作流（搜 → 选 → 联系 → 记录）
- 多步骤业务自动化（任何有"输入→等回复→处理"模式的场景）

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

## Act 层 — 真人化驱动（贝塞尔鼠标 + 生物识别打字律动）

Act 层 TYPE / SEND / CLICK 动作现已集成人类生物特征，底层调用：
- **human_mouse_click**: 三阶贝塞尔曲线 + cos S-curve 缓动 + 微幅抖动，替代直线瞬移
- **human_type_text**: 高斯按压时长 + 标点思维停顿（250~550ms），替代匀速 keyDown 循环
- **last_pos 贯穿**: 每次鼠标移动返回最新坐标，作为下次贝塞尔划行的起点

```python
# reactor._mouse_pos 贯穿全反应堆生命周期
self._mouse_pos = (100, 100)

# TYPE: JS 直接注入 value → 贝塞尔滑入聚焦 → 真人呼吸打字
self._mouse_pos = await human_mouse_click(self.cdp, inp_x, inp_y, current_mouse_pos=self._mouse_pos)
await asyncio.sleep(0.2)
await human_type_text(self.cdp, text)

# SEND/CLICK: 贝塞尔轨迹滑入按钮 → 物理按压
self._mouse_pos = await human_mouse_click(self.cdp, btn_x, btn_y, current_mouse_pos=self._mouse_pos)
```

**风控效果**: Mouse Tracking 捕获贝塞尔曲线点阵 + Keyboard Timing 捕获非匀速生物节律，双重真人化特征。

## Support 文件

- `references/decision-design.md` — 4 个核心设计决策的"为什么"(body_growing 替代 stopBtn / 18 周期阈值 / 状态锁冷却 / Enter 兜底)
- `templates/auto_chat_sop.json` — AI 自动对话 SOP 模板（8阶段，带 loops 和 self_heal 配置）
- `templates/1688_sop.json` — 1688 sourcing SOP 模板（5阶段：导航→搜索→选品→联系客服→记录）
- `scripts/diagnose_button_misidentification.py` — 按钮误识别静态探针

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
