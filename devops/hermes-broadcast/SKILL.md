---
name: hermes-broadcast
description: Use this skill when the user asks an IMPORTANT question, requests a multi-perspective answer, wants cross-validation across multiple AI models, mentions "多 AI 怎么看" / "broadcast" / "6 站同时问" / "交叉验证" / "几个 AI 一起答" / "调研一下" / "重要决策" / "知识验证", OR when a single-model answer is risky for a decision involving safety, data, architecture, or irreversible changes. Even if the user doesn't explicitly say "broadcast", trigger this skill when the question is high-stakes and a second/third opinion from ChatGPT, Gemini, Doubao, ChatGLM, DeepSeek, or Grok would be valuable. Do NOT use for trivial Q&A or quick learning — use `hermes -z` instead.
when_to_use: 重要技术决策 / 跨模型验证 / 高风险问题（涉及安全/数据/资源/不可逆操作） / 用户说"调研"/"多角度看"/"几个 AI 一起问"
---

# Hermes Broadcast — 6 站 AI 并行问答

**核心定位**: 把同一个问题同时扔给 **ChatGPT / Gemini / Doubao / ChatGLM / DeepSeek / Grok** 6 个已登录的 AI 站点，收集多角度答案交叉对比。

**适用场景**: 重要决策 / 技术调研 / 知识验证 / 跨模型一致性检查
**不适用**: 日常学习 / 简单查询 → 用 `hermes -z` 即可

---

## 触发判断（5 问自检 问自检）

接到一个问题，**0 思考**先过 5 问：

```
1. 这个答案会触发不可逆操作吗？（删数据 / 装软件 / 改生产配置）
2. 这个答案涉及安全 / 隐私 / 资金吗？
3. 单一模型的答案你敢直接采信吗？（怕幻觉 / 怕偏见）
4. 用户原话含 "broadcast / 6 站 / 多 AI / 调研 / 几个 AI 一起 / 交叉验证" 吗？
5. 单模型回答可能漏掉关键视角吗？

→ 任何一项 YES → 用 broadcast.py
→ 全部 NO → 用 hermes -z（更快更省）
```

---

## 真实接口（实测 2026-07-02）

**注意：主人原话里列的 flag（`--output json` / `--sites` / `--timeout` / `--probe`）我曾误写进 fact_store——实测 broadcast.py 当前**只支持位置参数**（问题文本）**，没有 argparse flag。本 skill 已修正。

```bash
# 唯一用法：位置参数 = 问题文本
python3 ~/.hermes/scripts/broadcast.py "你的问题"

# 退出码：0=全部成功 / 1=部分失败 / 124=超时
# 单站超时：120s（脚本内部 max_wait_s 默认值）
```

**Python API**（在 Hermes agent 内部用）：
```python
from broadcast import broadcast
results = await broadcast(
    "你的问题",
    cdp_url="http://localhost:9222"  # 默认就是 9222
)
# results: list[{site, answer, error?, latency_s}, ...]
```

---

## 6 站协议（实测 2026-07-02）

| 站 | URL | 输入框 selector | 抓回答方式 |
|---|---|---|---|
| ChatGPT | chatgpt.com | `div.ProseMirror#prompt-textarea` | network (backend-api/f/conversation) |
| Gemini | gemini.google.com | `div.ql-editor[contenteditable=true]` | innertext (model-response) |
| DeepSeek | chat.deepseek.com | `textarea[placeholder="给 DeepSeek 发送消息"]` | innertext (.ds-markdown) |
| Doubao | doubao.com | （略，见源码 STATIONS） | innertext |
| ChatGLM | chatglm.cn | （略，见源码 STATIONS） | innertext |
| Grok | grok.com | （略，见源码 STATIONS） | innertext |

**实现方式**: Playwright `connect_over_cdp` 复用 Chrome `--remote-debugging-port=9222` 已登录态。

**Chrome 启动前置条件**（必走）：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=~/.hermes/chrome-debug \
  --no-first-run --no-default-browser-check
```

**详见**: `hermes-see-act/SKILL.md` 的 "Chrome 启动 --remote-allow-origins=* 必带" 段（不能漏 `--remote-allow-origins=*`，否则 WebSocket 403）。

---

## Fallback：`broadcast_fallback.py`

**触发条件**（任意一种触发 fallback）：
- 主 broadcast 因 Network SSE 没拦截到失败
- 抓到了 footer 或历史消息（不是真回答）
- 40s 等待不够
- 输入框 selector 失效

**用法**：
```bash
python3 ~/.hermes/scripts/broadcast_fallback.py "你的问题"
```

**fallback 逻辑**：用 Playwright attach 已有 Chrome page，遍历 5 站（gemini/doubao/chatglm/deepseek/chatgpt）的 `SITE_SELECTORS` 字典，按"最后一条 message" 抓取（`:last-of-type` selector）。

**fallback 输出**：JSON 格式，每站单独结果。

---

## 决策矩阵（路 1 vs 路 2）

| 场景 | 用哪条路 | 延迟 | 成本 |
|---|---|---|---|
| 日常学习 / 简单 Q&A | `hermes -z "..."` | < 5s | 1 次 LLM 调用 |
| 快速查询（不需验证） | `hermes -z "..."` | < 5s | 1 次 LLM 调用 |
| **重要技术决策** | `broadcast.py` | 60-120s | 6 次 LLM 调用 |
| **知识验证 / 跨模 / 跨模型一致性** | `broadcast.py` | 60-120s | 6 次 LLM 调用 |
| **安全 / 隐私 / 不可逆操作** | `broadcast.py` | 60-120s | 6 次 LLM 调用 |
| broadcast 主站抓不到 | `broadcast_fallback.py` | 30-60s | 6 次 LLM 调用 |

**经验法则**：
- **L1 决策**（5 分钟内能撤的）→ `hermes -z`
- **L2 决策**（1 天能撤的）→ `hermes -z` 即可
- **L3 决策**（1 周才能撤的）→ `broadcast.py` 必走
- **L4 决策**（不可逆）→ `broadcast.py` + 用户二次确认

---

## 6 站登录态探活（数字人 SOP 必跑）

**会话启动 5 步自检**（proactive-execution v1.14.0 升级）应包含 broadcast 6 站探活：

```bash
# 1. Chrome CDP 在 9222?
lsof -i :9222 2>/dev/null | grep -q LISTEN && echo "CDP OK" || echo "❌ 启 Chrome debug"

# 2. broadcast 6 站探活（小问题不发，先看登录态）
python3 ~/.hermes/scripts/broadcast.py "ping" 2>&1 | head -20
# → 6 站都返回 = 全登录
# → 某站 503/timeout/cookie 失效 = 标"⚠️ 站 X 需重登"
```

**触发词**: "broadcast 探活 / 6 站登录态 / AI 站失效" → 0 思考跑这两步

---

## 踩过的坑（pitfalls）

- ❌ **不要先写 broadcast flag 再验真实接口**（2026-07-02 我犯的错）：主人原话列了 `--output json` / `--sites` / `--timeout` / `--probe`，我没实探就写进 fact_store。实测 broadcast.py 只支持位置参数，**没有 argparse**。**修法**: 写任何工具 skill 前 → 0 思考先 `python3 <script> --help` 实探，再写 description。
- ❌ **Chrome 没启 --remote-debugging-port=9222** → broadcast 报 "connect_over_cdp" 失败 → 0 思考按 hermes-see-act 段启 Chrome
- ❌ **Chrome 没带 --remote-allow-origins=*** → WebSocket 403（CSRF 防御） → 同上
- ❌ **broadcast 结果置信度低时** → 不是 broadcast 的锅，是问题本身问得不清楚 → 改写问题再 broadcast
- ❌ **broadcast 期望"6 站答案必须一致"** → 6 站答案不一致才是有价值的（暴露盲点）→ 不一致时让人工看，不是降级 hermes -z

---

## 跨渠道铁律

适用 **所有渠道** — CLI / Telegram / QQBot / Feishu / WeCom / Discord / 飞书 / API Server — 触发判断一致。

**用户在哪个渠道说"调研"** → 都用 `broadcast.py`（不是 hermes -z）

**详见**: `cross-channel-sop-sync` skill v3.1

---

## 关联

- `hermes-see-act` — Chrome debug 启动前置
- `proactive-execution` v1.14.0 — 会话启动 5 步自检（含 6 站探活候选）
- `cross-channel-sop-sync` v3.1 — 跨渠道行为一致
- `idle-learning-rounds` — A 方向脚本可考虑改 broadcast 探活

## 参考

- 脚本源码: `~/.hermes/scripts/broadcast.py` (332 行)
- 脚本源码: `~/.hermes/scripts/broadcast_fallback.py` (124 行)
- 主人原话: 2026-07-02 拍板"问 AI 有两条路"
- fact_store: ID 120-122 (决策规则 + 参数参考)