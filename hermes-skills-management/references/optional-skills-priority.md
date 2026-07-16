# Hermes 数字分身 — Optional Skills 优先级清单

## 核心发现（2026-07-11）

用户把 Hermes 定义为「住在电脑里的真人分身」，全网调研后结论：

**当前缺口（数字分身骨架）**

| 能力 | Hermes Optional Skill | 优先级 | 说明 |
|------|---------------------|--------|------|
| 💰 财务建模 | `3-statement-model` / `dcf-model` | ⭐⭐⭐ | 用户天天接触飞书财务表格，可直接对接 |
| 📧 邮件自动化 | `agentmail` | ⭐⭐⭐ | 重要通知不再漏 |
| 🗒️ 笔记知识库 | `siyuan` | ⭐⭐⭐ | 本地知识库，数字分身学习闭环 |
| 📅 日历/日程 | `here.now` | ⭐⭐ | 查日历可用性 |
| 🛒 电商监控 | `shop` / `shopify` | ⭐ | 订单/库存监控 |

## 安装建议（按优先级）

### 第一批（立刻装）
```bash
# 直接下载安装（hermes skills install 超时绕过）
python3 -c "
import urllib.request, os
base = '/Users/aimac/.hermes/skills'
skills = {
    '3-statement-model': 'https://raw.githubusercontent.com/NousResearch/hermes-agent/main/optional-skills/finance/3-statement-model/SKILL.md',
    'siyuan': 'https://raw.githubusercontent.com/NousResearch/hermes-agent/main/optional-skills/productivity/siyuan/SKILL.md',
    'agentmail': 'https://raw.githubusercontent.com/NousResearch/hermes-agent/main/optional-skills/email/agentmail/SKILL.md',
}
for name, url in skills.items():
    path = os.path.join(base, name, 'SKILL.md')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        content = r.read()
    with open(path, 'wb') as f:
        f.write(content)
    print(f'OK {name}: {len(content)} bytes')
"
```

## Optional Skills 全量清单（2026-07-11）

来源：[Hermes Optional Skills Catalog](https://hermes-agent.nousresearch.com/docs/reference/optional-skills-catalog)

### autonomous-ai-agents
antigravity-cli, blackbox, grok, honcho, openhands

### blockchain
evm, hyperliquid, solana

### communication
one-three-one-rule

### creative
baoyu-article-illustrator, baoyu-comic, blender-mcp, concept-diagrams, creative-ideation, hyperframes, kanban-video-orchestrator, meme-generation, pixel-art

### devops
inference-sh-cli, docker-management, hermes-s6-container-supervision, pinggy-tunnel, watchers

### dogfood
adversarial-ux-test

### email
agentmail ⭐

### finance ⭐
3-statement-model, comps-analysis, dcf-model, excel-author, lbo-model, merger-model, pptx-author, stocks

### gaming
minecraft-modpack-server, pokemon-player

### health
fitness-nutrition, neuroskill-bci

### mcp
fastmcp, mcporter

### mlops
huggingface-accelerate, axolotl, chroma, clip, dspy, faiss, guidance, huggingface-tokenizers, instructor, lambda-labs-gpu-cloud, llava, modal-serverless-gpu, nemo-curator, obliteratus, outlines, peft-fine-tuning, pinecone, pytorch-fsdp, pytorch-lightning, qdrant-vector-search, sparse-autoencoder-training, simpo-training, slime-rl-training, stable-diffusion-image-generation, tensorrt-llm, distributed-llm-pretraining-torchtitan, fine-tuning-with-trl, unsloth, whisper

### payments
mpp-agent, stripe-link-cli, stripe-projects

### productivity
canvas, here.now, memento-flashcards, shop, shopify, siyuan ⭐, telephony

### research
bioinformatics, darwinian-evolver, domain-intel, drug-discovery, duckduckgo-search, gitnexus-explorer, osint-investigation, parallel-cli, qmd, scrapling, searxng-search

### security
1password, godmode, oss-forensics, sherlock, unbroker, web-pentest

### software-development
code-wiki, rest-graphql-debug, subagent-driven-development

### web-development
cloudflare-temporary-deploy, page-agent

## 升级替代记录

- `humanizer-zh`（⭐37K，老）→ `avoid-ai-writing`（⭐2.2K，49模式，活跃维护）
  - 原因：模式少（24 vs 49），维护不活跃
  - 状态：humanizer-zh 已删除
