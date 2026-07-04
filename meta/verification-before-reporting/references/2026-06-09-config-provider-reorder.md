# Verification Before Reporting — Session Reference

## 2026-06-09 — 三个 provider 顺序调整（reorder-only） + Failure 16 经典案例

### Session 1: 误判 config providers 为空 → Failure 16

**Context**: User asked "现在 telegram/QQ/微信 默认是什么模型?"

**What I did wrong**:

1. `read_file ~/.hermes/config.yaml` with default `limit=500, offset=1`
2. Saw `providers: {}` (line 11, top-level empty dict under `model:`) + `model.default: MiniMax-M3`
3. Confidently reported: "current default is v2.aicodee.com MiniMax-M3, the 3 providers you mentioned don't exist, would need to create them as new entries"
4. **Never ran `wc -l`** to know config was 633 lines
5. **Never ran `grep -n`** to look for Apihub/agnes-ai/localhost/aicodee keywords

**What was actually true**:

- 633-line config.yaml
- The 3 providers (V2.aicodee.com, Apihub.agnes-ai.com, Local) were at **line 570-580**, in a flat list block registered as `custom_providers`
- The `providers: {}` I saw at line 11 was a **different section** (top-level model context) — not the providers the user was talking about

**User pushback signal**: "这个第一/第二/第三... 这明白吗" — the user had to paste the actual list because my first answer was wrong about "doesn't exist"

**Fix applied** (encoded as Failure 16 in SKILL.md):
- Always `wc -l` first
- Always `grep -n` for the relevant keywords
- Read by offset, not just "first page"

### Session 2: 三个 provider 顺序调整 — v3 "rearrange-only" 边界

**User's request** (paraphrased):
> "我重新来一个排序，/model Agnes-2.0-Flash --provider Apihub.agnes-ai.com作为所有的默认，http://localhost:3001/keys这个作为第二，/model MiniMax-M3-highspeed --provider custom:v2.aicodee.com放在第三"

**What the request actually meant** (interpreted from user's "明白吗" followup):

- (○) Apihub.agnes-ai.com (apihub.agnes-ai.com/v1) — agnes-2.0-flash
- (○) Local (localhost:3001) (localhost:3001/v1) — auto
- (●) V2.aicodee.com (v2.aicodee.com/v1) — MiniMax-M3 ← **currently active**

This is a 3-radio-button selector form. The user wants the relative order of the **3 existing provider entries** in the flat list at line 570-580 to be: Apihub first, Local second, V2.aicodee.com third.

**Why this is "v3 rearrange-only" and not a violation**:

- The 3 entries **already exist** — no "add new" needed
- Reorder is `[- V2.aicodee.com, - Apihub.agnes-ai.com, - Local]` → `[- Apihub.agnes-ai.com, - Local, - V2.aicodee.com]` — only positional change
- Each entry's `provider` / `base_url` / `api_key` / `model` / `label` fields stay identical
- `model.default` and `model.provider` (line 1-10) **stay as is** — V2.aicodee.com remains currently active (●)

**Pending action** (not executed this session — session ended before user gave final go-ahead):

1. Show user the current 3-entry list (line 570-580 verbatim)
2. Show the new 3-entry list (Apihub, Local, V2.aicodee.com order)
3. Explicit boundary check: "After this, Apihub becomes position 1 in the list, but the `model.default: MiniMax-M3` at line 2 is unchanged — V2.aicodee.com remains the actually-active provider. Confirm?"
4. User says "对" → execute the reorder via `patch` on the `^- name:` block, then re-read file to verify
5. **Don't touch**: `model:` block (line 1-10), `fallback_chain: ''` (line 7), `nv-nemotron-3-super` / `nv-deepseek-v4-flash` / `or-deepseek-chat-v3` (line 13-27, the older `fallback_providers:` list — separate from the user-requested 3)

**Lesson**: v3 规则 ("只调顺序不增不删") 的典型场景就是这种 — 现有列表重排, 字段不变, 长度不变。用户用 (○) / (●) UI 标记表达顺序, 是 Hermes/CLI 选择器的常见表达方式, **agent 必须分清"调顺序"和"改默认"是两件事**。

### Cross-references in this session

- `verification-before-reporting` Failure 16 — case study for "read the whole file before reporting"
- `script-provider-independence` v3 rules — case study for "rearrange-only" narrow window
- `user-profile` "模型解绑 v3" memory entry — same rules from session-memory side
