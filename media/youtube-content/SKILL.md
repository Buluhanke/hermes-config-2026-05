---
name: youtube-content
description: "YouTube transcripts to summaries, threads, blogs — plus 1688 sourcing intelligence, product comparison analysis, supplier selection reference, and automated channel monitoring."
platforms: [linux, macos, windows]
tags: [youtube, transcript, e-commerce, 1688, supplier, product-comparison, channel-monitoring]
last_updated: 2025-05-17
version: 2.0
---

# YouTube Content Tool

## When to use

Use when the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, or wants to extract and reformat content from any YouTube video. Transforms transcripts into structured content (chapters, summaries, threads, blog posts).

Extract transcripts from YouTube videos and convert them into useful formats.

## Setup

```bash
pip install youtube-transcript-api
```

## Helper Script

`SKILL_DIR` is the directory containing this SKILL.md file. The script accepts any standard YouTube URL format, short links (youtu.be), shorts, embeds, live links, or a raw 11-character video ID.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

1. **Fetch** the transcript using the helper script with `--text-only --timestamps`.
2. **Validate**: confirm the output is non-empty and in the expected language. If empty, retry without `--language` to get any available transcript. If still empty, tell the user the video likely has transcripts disabled.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
5. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

## Error Handling

- **Transcript disabled**: tell the user; suggest they check if subtitles are available on the video page.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Dependency missing**: run `pip install youtube-transcript-api` and retry.

---

# Extended: E-Commerce Intelligence (1688 / Supplier / Comparison)

These four specialized modes layer on top of the base transcript pipeline. Activate by specifying a mode keyword alongside the YouTube URL.

---

## Mode 1: 1688 E-Commerce Knowledge Extraction

**Trigger**: user says "1688", "sourcing", "货源", "拿货", "批发", "1688选品", "供应链知识"

**What it extracts**: Sourcing fundamentals, pricing mechanics, MOQ (Minimum Order Quantity), OEM/ODM workflows, shipping logistics, payment terms, and cross-border sourcing strategies.

**Extraction priorities** (extract from transcript in this order):
1. **Product categories** discussed — what types of products are being sourced
2. **MOQ and pricing tiers** — breakpoints and margin expectations
3. **Supplier selection criteria** — how to evaluate factories vs. trading companies
4. **OEM/ODM process** — customization workflow and tooling costs
5. **Shipping and logistics** — domestic CN shipping, international freight, fulfillment options
6. **Payment terms** — TT, L/C, Alibaba Trade Assurance, inspection terms
7. **Red flags** — warning signs of untrustworthy suppliers
8. **Tool/platform mentions** — 1688.com, Alibaba.com, Cainiao, WeChat, Pinduoduo

**Output template** (apply after fetching transcript):

```
## 1688 电商知识摘要 — [视频标题]

### 品类洞察
- 目标产品/品类：
- 适合渠道（亚马逊/eBay/独立站/线下）：
- 视频难度定位：□ 入门  □ 进阶  □ 专业

### 拿货核心参数
| 参数 | 值 |
|------|-----|
| 建议起订量（MOQ） | |
| 价格区间（¥） | |
| 物流方式 | |
| 交货周期 | |

### 供应商筛选要点
- 工厂 vs 贸易公司选择：
- 资质认证重要性：
- 样品流程：

### 关键风险提示
- ⚠️ [风险点1]
- ⚠️ [风险点2]

### 提到的工具/平台
- 平台：
- 工具：
```

**Example trigger phrases**:
- "这个1688视频讲的什么"
- "帮我提取这个货源视频的关键参数"
- "分析一下这个亚马逊选品视频"
- "货源供应链知识提取"

---

## Mode 2: Product Comparison Video Analysis

**Trigger**: user says "对比", "横评", "comparison", "测评", "哪个好", "评测"

**What it extracts**: Side-by-side comparison of multiple products — specs, price-to-performance ratio, use-case fit, pros/cons per product.

**Comparison extraction workflow**:
1. Identify **which products** are being compared (by name/brand/model)
2. Identify the **comparison dimensions** (price, quality, shipping, MOQ, customization, lead time)
3. Extract **per-product verdict** on each dimension
4. Identify the **overall recommendation** and **best for** (which use case / buyer type)
5. Note any **price claims** and verify they are fact or opinion

**Output template**:

```
## 商品对比分析 — [视频标题]

### 参评商品清单
| # | 商品/供应商 | 价位 | 主要优势 | 主要劣势 |
|---|-----------|------|---------|---------|
| A |            | ¥    |          |          |
| B |            | ¥    |          |          |
| C |            | ¥    |          |          |

### 核心对比维度
| 维度 | A | B | C | 推荐 |
|------|---|---|---|-----|
| 价格 |  |  |  |  |
| 质量 |  |  |  |  |
| MOQ  |  |  |  |  |
| 交货期 |  |  |  |  |
| 定制能力 |  |  |  |  |
| 售后 |  |  |  |  |

### 场景推荐
- **适合亚马逊FBA**：商品 [A/B/C]，原因：
- **适合小额试单**：商品 [A/B/C]，原因：
- **适合定制/OEM**：商品 [A/B/C]，原因：

### 关键结论
- 性价比首选：
- 质量首选：
- 最快交付：
```

**Example trigger phrases**:
- "这个对比视频哪个供应商好"
- "帮我分析这两个产品的优缺点"
- "横评总结一下"
- "哪个更适合亚马逊卖家"

---

## Mode 3: Supplier Selection Reference

**Trigger**: user says "供应商", "工厂", "选供应商", "供应商评估", "筛选", "supplier selection"

**What it extracts**: Supplier evaluation criteria, trust signals, red flags, due diligence checklist items discussed in the video.

**Evaluation dimensions** (extract claims, not just topics):
1. **Business type**: Manufacturer vs. Trading company vs. Wholesaler
2. **Verified credentials**: Alibaba Gold Supplier, BSCI, ISO, SGS reports
3. **Transaction history**: years on platform, response rate, repeat order rate
4. **Sample policy**: sample cost, sample lead time, refund policy
5. **Production capacity**: monthly output, machinery, worker count
6. **Communication quality**: response time, language fluency, technical understanding
7. **Pricing transparency**: FOB vs. CIF, moq clarity, hidden costs
8. **Red flags**: generic responses, stock photos, refused video calls, unusually low prices

**Output template**:

```
## 供应商选品参考 — [视频标题]

### 供应商评估维度
| 维度 | 重要性 | 视频建议 | 实际核查方法 |
|------|--------|---------|------------|
| 业务类型 | ★★★ |  |  |
| 资质认证 | ★★★ |  |  |
| 交易历史 | ★★☆ |  |  |
| 样品政策 | ★★★ |  |  |
| 产能规模 | ★★☆ |  |  |
| 沟通质量 | ★★★ |  |  |
| 报价透明度 | ★★★ |  |  |

### 红线指标（出现即淘汰）
- [ ] 不接受视频验厂
- [ ] 无法提供样品
- [ ] 价格低于市场价30%以上
- [ ] 无 Alibaba Trade Assurance
- [ ] 回复率 < 80%
- [ ] 无工厂实地照片/视频

### 优质供应商画像
- 业务类型：
- 最少年限：
- 样品政策：
- 价格区间：
- 沟通响应：

### 必做核查动作
1. [ ] 要求视频通话/工厂直播
2. [ ] 下单前先买样品
3. [ ] 用 Google Street View 核实工厂地址
4. [ ] 在 Alibaba 查交易记录和评价
5. [ ] 用 inspectBuyer.js 核对历史数据
```

**Example trigger phrases**:
- "帮我评估这个供应商视频"
- "选供应商要看什么"
- "工厂筛选标准是什么"
- "供应商尽调清单"

---

## Mode 4: Automated Channel Monitoring

**Trigger**: user says "监控", "monitor", "新视频", "更新通知", "订阅", "watch list", "自动检查"

**What it does**: Poll a YouTube channel for new videos, detect new uploads since last check, optionally notify.

**Implementation**: Python script that reads a channel RSS feed (faster, no auth required) and compares against a local JSON checkpoint file.

**Setup**:
```bash
# Install dependency
pip install feedparser
```

**Script**: `SKILL_DIR/scripts/monitor_channel.py`

**Usage**:
```bash
# Add a channel to the watch list
python3 SKILL_DIR/scripts/monitor_channel.py --add "CHANNEL_URL_OR_ID"

# Check all watched channels for new videos
python3 SKILL_DIR/scripts/monitor_channel.py --check-all

# Check a specific channel
python3 SKILL_DIR/scripts/monitor_channel.py --channel "CHANNEL_ID" --check

# Show watch list
python3 SKILL_DIR/scripts/monitor_channel.py --list

# Remove a channel
python3 SKILL_DIR/scripts/monitor_channel.py --remove "CHANNEL_ID"

# Enable Telegram notification (set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
python3 SKILL_DIR/scripts/monitor_channel.py --notify --channel "CHANNEL_ID"
```

**Checkpoint file**: `~/.hermes/youtube-content/channel_checkpoints.json`

**RSS-based channel ID extraction**:
```bash
# Extract channel ID from a YouTube channel page URL
python3 SKILL_DIR/scripts/monitor_channel.py --resolve "https://www.youtube.com/@username"
```

**Example trigger phrases**:
- "监控这个频道的新视频"
- "帮我追踪这几个1688卖家频道"
- "有新品通知我"
- "自动检查这个频道的更新"

**Automated polling via cron** (optional, macOS launchd also works):
```bash
# Run every hour, check all channels, notify on new videos
# Add to crontab: 0 * * * * /usr/bin/python3 /Users/aimac/.hermes/skills/media/youtube-content/scripts/monitor_channel.py --check-all --notify >> ~/.hermes/logs/youtube-monitor.log 2>&1
```

**Example workflow**:
1. User shares a channel URL → resolve channel ID → add to watch list
2. Cron job runs hourly → fetches RSS → diffs against checkpoint → prints new video list
3. If new videos found and `--notify` enabled → sends Telegram message
4. User asks to summarize a new video → falls back to base transcript pipeline

---

## Combined E-Commerce Workflow Example

A typical session combining multiple modes:

```
User: "https://youtube.com/watch?v=XXXXX 是讲1688拿货的，帮我分析供应商评估要点"

1. Fetch transcript with --timestamps
2. Apply 1688 Extraction mode → extract supplier evaluation dimension
3. Layer in Supplier Selection Reference mode → cross-reference the video's criteria against the evaluation template
4. Output combined report

User: "帮我监控这个频道，有新品通知我"

1. Resolve channel ID from URL
2. Add to watch list
3. Explain cron setup or ask to enable Telegram
4. Confirm with: "已添加 [频道名] 到监控列表，每小时检查一次"
```

---

## Key Chinese E-Commerce Terminology Reference

When processing Chinese-language transcripts, map terms consistently:

| 中文 | English | Notes |
|------|---------|-------|
| 拿货 | Sourcing / Procurement | |
| 起订量 (MOQ) | Minimum Order Quantity | |
| 来样订做 | OEM / Sample-based manufacturing | |
| 贸易公司 | Trading Company | Middleman, not manufacturer |
| 厂家直销 | Factory Direct | |
| 拿样 | Sample Order | Usually paid |
| 散拿 | Bulk without branding | |
| 拿货价 | Sourcing Price | First-tier price |
| 二代/三级代 | 2nd/3rd tier agent | More expensive, smaller MOQ |
| FOB | Free On Board | Seller delivers to port |
| CIF | Cost, Insurance, Freight | Seller pays freight + insurance |
| 验厂 | Factory Audit / Inspection | |
| 空运/海运 | Air freight / Sea freight | |
| 报关 | Customs Declaration | |
| 1688货源 | 1688 Product Sourcing | Alibaba's domestic CN platform |
