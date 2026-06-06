# Multi-Site Cross-Validation + 9-Dimension Self-Assessment（2026-06-05）

## 用途

跑多个 AI 站同时问同一个问题 → 拿到 N 份答案 → 交叉对比 → 选最优方案执行。

跟 `multi_ask_v3` 的区别：
- `multi_ask_v3`（在 `ai-site-browser-e2e` skill）= **发问题 + 抓回复的工程化**（输入/读取/收信）
- **本文档** = **拿到回复后的交叉对比 + 否决违反硬规则的 + 自评 9 维度**

## 触发条件

- 用户说 "跑一遍看看几个" / "问 AI 网站" / "交叉验证" / "全网搜索"
- 用户给了 1 个调研问题，希望从 N 个 AI 视角看
- 需要选**最优方案**而不是只看 1 个 AI 的答案

## 6 步工作流（2026-06-05 实测）

### Step 1: 跑前 checklist（按 14:00 硬规则 + ai-site-browser-e2e preflight）

- Chrome 9333 跑着（system Default profile，cookies 共享）
- 4 站登录态在（Claude/豆包/智谱/Grok 至少 3 个，cookies 文件可查）
- 反指纹 12 项全绿（`anti_detect_inject.py --port 9333 --verify`）

### Step 2: 问所有站同一个问题

**问题设计原则**（实测有效）：
- 给**具体上下文**（本机型号 + 配置 + 当前状态）— 不要泛泛问
- 让 AI **按优先级排前 5**（要排序，不要平铺）
- 让 AI **给具体到本机的命令/工具/SKILL 路径**（不要抽象建议）
- **200 字内** 限制（强迫 AI 收敛到最关键 5 条）

**实测提问模板**（已用于 9 维度评估）：
> "我是 Mac mini M4 24GB 跑 Hermes Agent 真人化助手（67 技能 + Claude/豆包/智谱/Grok 4 站登录态 + Chrome 9333 CDP + Ollama 5 本地模型 + macOS 26.5），目标是 9 维度全 100 分：①看 ②想 ③说 ④做 ⑤学 ⑥防 ⑦跑 ⑧连 ⑨活。请你按优先级排前 5 个最该补的能力 + 具体到我这台机器可执行的下一步（不要泛泛，要具体的命令/工具/SKILL 路径）。200 字内。"

**分发策略**：
- 3 站用 `browser_navigate` + `browser_type` + `browser_press('Enter')`
- 4 站全发完等 60 秒（Claude/Grok 慢，豆包/智谱快）
- 切回 tab 用 `browser_navigate(url)` 拉回复（点击历史对话）

### Step 3: 拿回复（CDP 直接读，避免 snapshot 截断）

```python
# 避免 browser_snapshot 截断 (limit 8000 chars)
# 直接 CDP Runtime.evaluate 读 main 区
browser_cdp(method="Runtime.evaluate",
            params={"expression": "document.body.innerText.substring(0, 6000)",
                    "returnByValue": True},
            target_id=grok_tab_id)
```

**注意**：CDP `returnByValue` 必须是 raw JSON true（不是 Python `True`），否则报 "BINDINGS: bool value expected at position 77"。

### Step 4: 交叉对比表（核心产物）

| 维度 | 站 A | 站 B | 站 C | **共识度** |
|---|---|---|---|---|
| **#1 优先** | ... | ... | ... | 共识/独有 |
| **#2** | ... | ... | ... | ... |
| **#3** | ... | ... | ... | ... |
| **#4** | ... | ... | ... | ... |
| **#5** | ... | ... | ... | ... |

**共识维度**（≥2 站提到）= 高置信度，优先做
**独有维度**（1 站）= 看理由是否充分（有时候 1 站说得最清楚的最对）
**冲突维度**（站间互斥）= 用硬规则筛（违反硬规则的直接否决）

### Step 5: 否决违反硬规则的（这一步最关键）

**实测捕获的 1 条**（来自豆包 #3）：
> "pkill -f 9333; chrome --remote-debugging-port=9333 --headless=new" 

→ **直接否决**，违反 14:00 硬规则（**必须本机已登录 Chrome，不要 --headless**）

**否决清单的判据**：
- 跟 14:00 硬规则冲突 → 否决
- 跟 14:50 模型解绑硬规则冲突 → 否决
- 跟 14:00 "破坏性删除必须授权" 冲突 → 否决
- 跟 macOS 资源约束冲突（24GB 总内存，杀完后剩 < 2GB）→ 否决

### Step 6: 输出最终方案 + 9 维度自评

**最终方案表**：
| 优先级 | 行动 | 来源 | 是否违反硬规则 |
|---|---|---|---|
| P0 #1 | ... | Claude #1 | ✅ |
| P0 #2 | ... | 智谱 #1 + 豆包 #1（合并）| ✅ |
| ... | ... | ... | ❌ 否决理由 |

**9 维度自评框架**（每个维度打 0-100 分）：

| 维度 | 含义 | 现状 | 分数 | 差什么 |
|---|---|---|---|---|
| ① 看 | 视觉/OCR/VLM | CDP DOM 100% + 无 VLM 识图 | 70 | screencapture + llava |
| ② 想 | 推理/记忆/RAG | fact_store 92% + FTS5 + Ollama 5 模型 | 85 | 缺 RAG 向量 |
| ③ 说 | 语音/对话路由 | TTS + STT + 5 模型 | 70 | 5 模型没路由 |
| ④ 做 | 控制/执行 | 67 技能 + CDP + terminal | 80 | 不缺 |
| ⑤ 学 | 多站交叉 | **已跑通**（这次 3 站交叉）| 90 | 增量蒸馏 |
| ⑥ 防 | 反爬/反测/防注入 | stealth + 4 站登录 | 75 | CDP 指纹隐藏 |
| ⑦ 跑 | 性能/资源 | 5+ cron + mem_patrol | 85 | sysctl shmmax |
| ⑧ 连 | 多通道 | 5 通道 + 4 AI 站 | 75 | 缺 webhook / bus |
| ⑨ 活 | 自愈/保活 | mem_patrol + cleanup + keepalive | 75 | watchdog |

**加权平均 ≈ 78 分**（不是 100 分）

## 反面教材（今天实测 3 次踩坑）

### 1. 5 站全开 + 同时发问 → 抢 CDP 上下文

**症状**：发完 Grok 后 navigate 回豆包 → 豆包历史对话里**没有**新发的问题。

**根因**：browser_navigate 切 active tab 改变了 CDP context，**新发的输入框被旧 tab 上下文抢了**。

**修法**：发完 1 站后等 5 秒再切下 1 站，**或者** 4 站开 4 个 tab 不切换，每站发完后单独 snapshot。

### 2. 4 站同时用 Enter 发送 → 30% 没触发

**症状**：豆包/智谱 Enter 发送成功，但 Grok/Claude 概率性没触发。

**根因**：Grok/Claude 用 ProseMirror contenteditable，Enter 被前端框架拦截做"换行"而不是"发送"。

**修法**：等 30 秒看 main 区是否出现"我的问题"+ AI 回答；没出现 → 手动 click 发送按钮（Claude 右侧的 ↑ 按钮）。

### 3. snapshot 截断 8000 chars → 长答案只看到一半

**症状**：Grok 答案 96 行，snapshot 只显示"思考了 11s" 后面被截断。

**根因**：browser_snapshot 限制 8000 chars。

**修法**：直接用 `browser_cdp(method="Runtime.evaluate", ...)` 读 `document.body.innerText`，**一次拿 6000 chars**，需要时分页读。

## 已知 AI 站回复时间（实测）

| 站 | 思考时间 | 回复速度 | 备注 |
|---|---|---|---|
| Claude | 8-15s | 30-60s 流式 | "finished the response" 状态出现才算完 |
| 豆包 | 5-10s | 20-40s 流式 | "新对话" 标题出现 = 收到 + 开始生成 |
| 智谱 | 3-8s | 15-30s 流式 | 最快，"思考结束" 状态 |
| Grok | 8-12s | 20-40s 流式 | "思考了 11s" 后流式 |

**默认 60 秒** 等 4 站都回复完，再开读回复流程。

## 持久化产物

把"3 站交叉对比表 + 否决清单 + 9 维度自评 + 最终方案"写到 `~/Obsidian/迅龙贸易/AI进化/cross-validation/YYYYMMDD-<topic>.md`，方便未来 review。

```bash
OUT=~/Obsidian/迅龙贸易/AI进化/cross-validation/$(date +%Y%m%d)-mac-mini-m4-agent-9-dimension.md
mkdir -p "$(dirname "$OUT")"
cat > "$OUT" << 'EOF'
# 2026-06-05 Mac mini M4 Hermes Agent 9 维度评估
## 3 站交叉对比表
| ... |
## 否决清单
- 豆包 #3 chrome --headless (违反 14:00 硬规则)
## 9 维度自评
| 维度 | 现状 | 分数 |
| ... |
## 最终方案（按 P0/P1 排）
| 优先级 | 行动 | 来源 |
| ... |
EOF
echo "✅ 写到 $OUT"
```
