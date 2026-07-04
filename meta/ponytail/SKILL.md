---
name: ponytail
description: Ponytail 6 步决策梯 — 写代码前 0 思考走 YAGNI → stdlib → native → installed → one-line → minimum。踩过的反模式：自己造 wrapper / 不搜现成方案 / 装包不集成 / 写 100 行干 1 行的事。
when_to_use: 任何需要写新代码/新脚本/新 wrapper 的任务。Hermes 接到"做 X"指令时，先问"现成方案在哪"再动手。
---

# Ponytail FULL MODE — 6 步决策梯

**来源**: github.com/DietrichGebert/ponytail (29.6k stars)
**实测**: 5 个 LLM × 5 任务减代码 77-94%
**核心**: The best code is the code never written. Deletion over addition.

## 6 步梯（按顺序，能在第一级停就停）

```
1. YAGNI       → 这东西真的需要存在吗? 不需要就别写
2. stdlib      → 标准库已经做这事? 用标准库
3. native      → 平台/系统原生覆盖? 用原生的
4. installed   → 已装依赖能解决? 用现成的
5. one-liner   → 能写成一行? 写成一行
6. min code    → 写完才最小能 work 的代码
```

**绝不能省的**（即使 Ponytail 模式）：
- 输入验证 / 错误处理 / 安全 / 可访问性
- 数据丢失处理 / 信任边界
- 用户明确要求的行为
- 非平凡逻辑的 1 个最小可运行 check

## 实测反模式（Hermes 自己踩过的）

### 反模式 1: 自己写 wrapper 包现成方案
- ❌ 写 `fetch_transcript.py` 100 行 → yt-dlp + youtube-transcript-api 是事实标准
- ❌ 写 MoA 配置 yaml → `hermes moa configure` 命令直接做
- ❌ 写"屏幕识别 4 通道方案" → cua-driver MCP + screencapture 系统工具已装

### 反模式 2: 装包不集成
- ❌ 装 scrapling → 不集成 → 浪费磁盘
- ❌ 装 crawl4ai 子命令包装 → 不调 → 占 venv
- **修法**: 装前先搜"这个包当前任务是不是真用得上"，装后立即在调用链里跑一次

### 反模式 3: 不搜现成方案
- ❌ 写"读视频字幕"功能 → 没搜"youtube transcript 2026 best practice"
- ❌ 写"统一 wrapper" → 没搜 `web-content-fetcher` / `fetch_url` 是否已存在
- **修法**: 写任何 ≥ 10 行代码前，先 `web_search "X best practice 2026"` + `find ~/.hermes/skills -iname "*X*"`

### 反模式 4: 100 行干 1 行的事
- ❌ fetch_transcript.py 100 行 → 实际 1 行 yt-dlp + 1 行 youtube-transcript-api 调用

## 触发词（看到这些词 → 0 思考走 Ponytail）

- "写个脚本" / "做个工具" / "实现一下"
- "帮我装 X"（装前先问"现成方案是不是已经满足"）
- "我看 X 不太好用" → 先搜现成替代，别自己改

## SOP：接到任务后 30 秒内

1. **30 秒搜**: `web_search "X 2026 best practice"` + `find ~/.hermes/scripts -iname "*X*"`
2. **看现成**: 找到就用，没找到才写
3. **写也最小**: 写完跑 1 次确认 work，不写 wrapper 不写抽象
4. **删除优先**: 旧脚本/旧配置 → 立刻删（user v3.0: "破坏性删除才授权"，普通删除直接干）

## 关联

- AGENTS.md: 6 步决策梯 + 引用来源
- hermes-agent skill: 配置类任务优先 load
- user profile v2.1.1: "有问题默认修" — 但修前先搜现成修法
- user profile v3.1: "不要问要不要，直接做" — 但"做"前先搜现成做

## 不在 Ponytail 范围（按 v3.0 例外）

- 不可逆操作（rm -rf ~/ / 格式化 / 改生产）仍单人确认
- 24GB 硬件红线不破
- 信任边界（API key / cookie / 用户隐私）不能"省"
