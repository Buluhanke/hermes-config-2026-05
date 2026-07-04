---
name: ponytail-decision-ladder
description: Use when deciding whether to write new code/script/install a new dependency. Lazy senior dev workflow — stop at the first rung that holds (YAGNI → stdlib → platform-native → installed-dep → one-liner → minimal code). Load when user mentions "do I need to write this", "Ponytail", "lazy", "YAGNI", "don't over-engineer", or when tempted to build a new tool from scratch.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [workflow, decision-making, code, ponytail, yagni, lazy, hermes-style]
    related_skills: [proactive-execution, verification-before-reporting, hermes-mac-os-agent]
triggers:
  - "Ponytail"
  - "YAGNI"
  - "要不要写个脚本"
  - "给我写个 X"
  - "装个新框架"
  - "做个新工具"
  - "别造轮子"
  - "lazy"
  - "do I really need this"
  - "别过度设计"
  - "do I need to write code"
---

# Ponytail Decision Ladder — 写代码前的 6 步决策梯子

## Overview

A "lazy senior dev" workflow for the moment when someone asks you to **build X** or **install Y**. Stops at the first rung that holds — never writes code that an existing tool, dependency, or platform feature already covers. Drawn from `github.com/DietrichGebert/ponytail` (29.6k stars) + 6 LLM eval: 77-94% code reduction, behavior preserved.

**Iron rule**: only proceed when the rung you're standing on genuinely doesn't hold. "It works but I want it my way" is not a reason to drop to a lower rung.

## When to Use

- User asks "build me a scraper / write a wrapper / install a framework"
- User explicitly invokes "Ponytail" / "lazy" / "YAGNI" / "不要造轮子"
- You feel the urge to `write_file` a new Python module
- Deciding between "use existing tool X" vs "build new tool Y"
- Evaluating a list of candidate tools ("which of these should I install?") and want the smallest-effective answer

## When NOT to Use

- The task genuinely requires new behavior (genuine gap, not preference)
- Existing tools all fail verified tests (Failure 23 / 30 / 40 discipline)
- User has explicitly asked for the code (not just the capability)

---

## The 6-Rung Ladder

Stop at rung N when it holds. Don't drop to rung N+1 without a real reason.

### Rung 1: YAGNI — does this need to exist at all?

**Question**: "Will I actually call this more than once? Is the user asking for a *capability* or a *deliverable*?"

**Default**: No. Most "write me a script" requests are satisfied by typing the right command once.

**Stop here if**: the task is one-shot, the user just wants the output, or the "script" is really "run 3 commands in sequence" which is fine as a one-liner.

**Real case (this session)**: User asked "install 11 crawler tools" → I evaluated each, **identified the 1 with unique value (Agent-Reach)**, declined the other 10 instead of installing all. Agent-Reach alone covered the underlying need.

### Rung 2: Stdlib — does the standard library cover it?

**Question**: "Is there a Python/Node/Go stdlib module that does this?"

**Common stdlib wins**: `urllib.request` for HTTP, `json` for parsing, `sqlite3` for local DB, `pathlib` for paths, `subprocess` for shell, `csv` for tabular, `html.parser` for HTML.

**Stop here if**: any stdlib module gives you the primitive. Note: stdlib *quality* varies (Python's `urllib` is verbose; Node's got `fetch` now), so "stdlib exists" ≠ "stdlib is best" — it's just a rung.

### Rung 3: Platform-native — does the OS / runtime have a built-in?

**Question**: "Is there a macOS / Linux / Windows / Chrome command that already does this?"

**Common wins**:
- macOS: `screencapture`, `osascript`, `defaults read`, `mdfind`, `lsappinfo`, ScreenCaptureKit, AX API
- Linux: `xdotool`, `xclip`, `notify-send`, `dbus-send`
- Windows: PowerShell + WMI
- Browser: CDP `Page.captureScreenshot`, `Runtime.evaluate`, AX tree

**Stop here if**: a platform tool gives you the capability with fewer dependencies.

**Real case**: Read screen on macOS → AX tree (mcp_cua_driver) 80ms, not screenshot+VLM 3-8s. Read video captions → DOM `.ytp-caption-segment` 0ms, not OCR 900ms.

### Rung 4: Installed dependency — does something you already have cover it?

**Question**: "Is `agent-reach`, `web_extract`, `browser_*`, `mcp_chrome_devtools_mcp_*`, or any other already-installed tool good enough?"

**Common wins**: 
- Reading any URL → `web_extract` (built into Hermes toolset)
- Reading a JS page → `browser_*` (CDP via Chrome 9222) or `chrome-devtools-mcp`
- Sending a Telegram message → `hermes send -t telegram`
- Reading chat reply → `Runtime.evaluate` on already-open tab

**Stop here if**: an installed tool does the job. Don't install new things when existing ones suffice.

**Real case (this session)**: User listed 11 scrapers. Of those, **7 had direct equivalents already installed** (web_extract, browser_cdp, agent-reach's yt-dlp, etc.). I refused to install duplicates. Agent-Reach got installed because it had no equivalent.

### Rung 5: One-liner — can the existing tool do it in a single command?

**Question**: "Will `web_extract(url)` or `curl -X POST | jq .` solve this without writing a wrapper?"

**Stop here if**: the existing tool's CLI/script interface gives you what you need. Don't write a Python wrapper around `yt-dlp` when you can call `yt-dlp` from a shell command.

**Real case**: Reading YouTube captions → `yt-dlp --list-subs URL` then `yt-dlp --write-auto-sub -o "/tmp/yt_test/%(title)s.%(ext)s" URL`. No Python needed.

### Rung 6: Minimal code — only NOW you write

**Question**: "What's the smallest script that adds the gap?"

**Discipline**:
- 5-30 lines is the sweet spot
- No abstractions (no class, no factory, no config file)
- Hardcode paths and values that you actually use
- One main purpose per script
- Reuse the standard library + installed dependencies from rungs 2-4

**Never**:
- > 200 lines without consulting a human
- A new dependency just for one feature
- A wrapper around something with a CLI
- A config file when env vars / hardcoded values work
- A class when 3 functions work

**Stop here if**: you really do need to write code. Stop the ladder and write the minimum.

---

## Common Anti-Patterns (Ponytail violation signals)

These are the patterns where the ladder got dropped. Spot them and reverse.

| Anti-pattern | Why it's wrong | Right approach |
|---|---|---|
| "I'll write a wrapper around X" | X already has a CLI; the wrapper adds zero capability | Call X directly (rung 5) |
| "Let me make it configurable" | YAGNI; no one will change the values | Hardcode; refactor when needed (rung 1) |
| "I'll add error handling for all cases" | Most error paths never fire | Let it crash; handle the 1 path that did |
| "I'll write tests" | > 30 lines → too much code → rung ladder wrong | Reject rung 6; drop back up |
| "I'll add a CLI interface" | You are the only user; the script IS the CLI | Hardcode; run from your tool |
| "I'll create a new directory structure" | Flat is fine until it isn't | Put files where they naturally go |
| "Let me add typing/docstrings/logging" | Each adds lines without behavior change | Comment-free minimal code |

## Verification Before Climbing Down

Before dropping a rung, verify:

1. **Does the higher rung actually work?** Run it once. Don't assume.
2. **Is the gap real or perceived?** "It's not as clean" ≠ gap.
3. **Is the time cost of writing code worth less than the time cost of using the imperfect higher-rung tool?** Usually no.

If the answer to (1) is "no, it doesn't actually work" or (2) is "real", drop a rung. Otherwise stay.

## Failure Mode: Stuck at Rung 1 When User Wants Rung 6

Sometimes the user *wants* a real script. Examples: "make me a CLI", "I want to call this from cron", "I need this runnable on a fresh machine with no LLM". 

These are valid. When user says so, skip the ladder and go to rung 6 with minimum code. But:
- Default to rung 1-5 anyway unless explicit
- "I'll give you a script" is a hint, not a final answer — still offer rung 5 first

## Trigger Words (when this skill should load)

- "Ponytail"
- "YAGNI"
- "lazy"
- "write a script"
- "make a tool"
- "build a wrapper"
- "install X"
- "do I need to write code"
- "stop over-engineering"
- "minimum code"
- "don't add abstractions"

## Related Skills

- `proactive-execution` — once you've decided what to build, this governs how you ship it (no clarifying questions, ship when ready)
- `verification-before-reporting` — after running the chosen path, verify it actually worked (Failure 30: "全部修复" must be tested item-by-item)
- `hermes-mac-os-agent` — when the decision is "use macOS native", this is the architecture

## Reference Files

- `references/2026-06-27-session-case-studies.md` — real case studies from a single session where the ladder was applied (install 11 tools → install 1, YouTube captions → 0 code, etc.)
- `references/2026-06-27-toolchain-consolidation.md` — v1.1.0 新增: fetch_url.py 已存在就**别写 wrapper** 实战 + 删死代码 5 个 (scrapegraphai/wechat-article-for-ai/xiaoyuzhou/html2text/web-content-fetcher) + Ponytail "已存在的工具 = rung 4" 边界

## One-shot Decision Examples (real session cases)

**Case 1**: "Install 11 crawler tools"
- Rung 4: `web_extract`, `browser_cdp`, `yt-dlp` (via agent-reach) already cover most needs
- Result: installed only `agent-reach` (gave YouTube + B站 + RSS + semantic search + GitHub + Twitter all at once via one CLI). Declined the other 10.

**Case 2**: "Read the captions on this YouTube video"
- Rung 3: `yt-dlp` is already installed (via agent-reach)
- Rung 5: single command — `yt-dlp --list-subs URL`
- Result: zero new code, captions returned

**Case 3**: "Read screen on macOS"
- Rung 3: ScreenCaptureKit via `mcp_cua_driver_take_screenshot` (already there)
- Rung 5: single tool call
- Result: zero code written, vision attained

**Case 4**: "Translate these 11 crawler tools to see which fits"
- Rung 1: do not translate; check rungs 2-5 against each
- Rung 4: most are duplicates
- Result: short list of "actually new" tools, declined the rest

**Case 5**: "Write me a YouTube caption fetcher Python script"
- User asks explicitly for the script. **Skip to rung 6**, but keep minimum:
  ```python
  import subprocess, sys
  url = sys.argv[1]
  subprocess.run(["yt-dlp", "--write-auto-sub", "--sub-lang", "en.*", "-o", "/tmp/cap.%(ext)s", url])
  ```
- 3 lines. Hardcoded paths. Single purpose. Stop here.

**Case 6 (2026-06-27 实战 v1.1.0)**: "既然很多安装了又不被调用的，那就全部连接起来固化"
- 用户要求"装机 + 固化 + 删死代码" → 我跑 Ponytail 全 6 步：
  1. **Rung 1 (YAGNI)**: 11 个装机需求 → 评估真值 → agent-reach 一个顶 7 个 (YouTube/B站/V2EX/RSS/Twitter/GitHub/全网搜索)
  2. **Rung 4 (installed deps)**: `~/.hermes/scripts/fetch_url.py` v2 (Trafilatura + DiskCache + Playwright upgrade) **已存在并 work** → 不要再写 wrapper
  3. **Rung 5 (one-liner)**: 加 `fetch_transcript.py` 是**真缺口**（fetch_url 没 YouTube/B站路由）→ 但仍是最小化：100 行，2 个函数 (fetch_youtube via youtube-transcript-api, fetch_bilibili via yt-dlp)
  4. **Rung 6 (minimal code)**: fetch_transcript.py 不精简到 3 行 (Case 5 那种) 因为 YouTube/B站路由 + JSON/text 双格式输出需要结构
- **关键 Ponytail 决策点**: "fetch_url.py 已存在" = **停止在 rung 4**，不写 wrapper；"YouTube/B站字幕" = **真缺口**才下 rung 6
- **删死代码 5 个**: scrapegraphai (import 失败 langchain ChatOllama 移除) + wechat-article-for-ai (agent-reach 捆绑无人调) + xiaoyuzhou (agent-reach 捆绑无人调) + html2text (web-content-fetcher 必需但**误删一次再装回**) + web-content-fetcher 整仓 (被 fetch_url + fetch_transcript 覆盖)
- **反面案例 (本次踩坑)**: html2text 我第一次"按死代码"删了，但 web-content-fetcher 的 fetch.py 依赖它 → fetch_url 实际不依赖它，但 fetch_url 的 fallback 链 (`extract_main`) 用 html2text 兜底 → 删完报错 → 重装回去。**修法**: 删依赖前必 `grep -rn "from html2text\|import html2text" ~/.hermes/scripts/` 查所有反向依赖，**别只查主包依赖**
- **触发词新增**: "已存在/覆盖/不要写 wrapper/重复造轮子" → 0 思考 rung 4 停；"真缺口/没覆盖/没路由到" → 0 思考 rung 6 下

**Case 7 (2026-06-27 实战 v1.1.0)**: Ponytail "已存在工具 = rung 4" 的边界测试
- 场景: 装机后用户说"全部连接起来固化"
- 错误思路 1: "写一个统一 wrapper fetch_content.py 调度所有工具" → 违反 YAGNI，fetch_url.py 已是 wrapper
- 错误思路 2: "fetch_url.py 缺 YouTube 路由就改 fetch_url.py 加进去" → 违反单一职责，fetch_url 跟 fetch_transcript 是 2 个 domain
- 正确思路: fetch_url.py 已有 = 不动；fetch_transcript.py 是新 domain（新写最薄 100 行）；固化 = 删死代码不重写
- **Ponytail 5/6 边界**: 当 rung 4 命中但**有缺口**（不是 100% 覆盖），才下 rung 6；如果 rung 4 完全覆盖，**绝不**下 rung 6
- **触发词**: "fetch_url 没有 X / fetch_url 不覆盖 / 调度到 Y" → 先判"X/Y 是 fetch_url 的 domain 还是新 domain?" 是新 domain → 写新文件；是 fetch_url 的 domain → patch fetch_url 加进去

**Case 8 (2026-07-03 实战)**: "不要擅自写代码，用最简单的方式" — API测试场景的Ponytail应用

用户原话: "再好好深度检查一下" + "不要擅自写代码，用最简单的方式就行"

**反面案例 (本次真发生)**:
- 任务: 检查两个模型(agnes-2.0-flash / nv-qwen3.5-397b)的API配置是否正确
- 我做的: 先写 python subprocess 脚本读 .env 绕过 source 报错，再 curl 测 API
- 用户纠正: "不要擅自写代码，用最简单的方式"
- 根因: 习惯性想到"写个脚本处理"而不是"直接 curl"; config.yaml 里已经有provider配置，直接测就行

**正确做法 (本session验证有效)**:
```
# 1. 直接用 curl 测 API (最简单)
curl -s --connect-timeout 10 -X POST "https://apihub.agnes-ai.com/v1/chat/completions" \
  -H "Authorization: Bearer ${AGNES_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"agnes-2.0-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# 2. 脱代理测真实错误码 (关键，避免代理掩盖)
unset https_proxy http_proxy && curl ...

# 3. gateway API 兜底 (gateway 在跑就直接用)
curl -s http://127.0.0.1:8642/health

# 4. 看 config 而非写代码
cat ~/.hermes/config.yaml | grep -A5 fallback_providers
```

**触发词**: "用最简单的方式/不要写代码/直接测/不要写脚本" → 立即 curl / gateway API / cat grep，不用 python subprocess 绕

**Case 9 (2026-07-04 实战)**: 用 `sed` 改配置 vs 写 Python

用户: "不要乱自己写代码，一定要先网上找"

场景: 要把 config.yaml 里 nv-qwen 的 timeout 从 20s 改成 120s。

- ❌ 我先尝试写 Python subprocess 脚本去 grep/改 yaml → 结果 `yaml.dump()` 把 providers dict 变成 list，配置彻底坏掉，还原花了 10 分钟
- ✅ 正确做法: `sed -i '' '21s/20/120/' ~/.hermes/config.yaml` 一行改完，格式不变

教训: config.yaml 改单行值 → `sed -i '' '行号s/旧/新/' 文件`；YAML 结构破坏无法用 python 序列化修复（json/dict 映射丢失）；修改前先 web_search 查是否已有官方/社区解法