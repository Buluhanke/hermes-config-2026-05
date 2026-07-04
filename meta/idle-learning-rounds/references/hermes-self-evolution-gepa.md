# Hermes Agent Self-Evolution（DSPy+GEPA）参考

**Source**: [NousResearch/hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution) ⭐4.5k MIT · ICLR 2026 Oral
**采集时间**: 2026-07-02 08:01 cron idle 学习

## 核心定位

Hermes 官方自进化 pipeline：用 **DSPy + GEPA（Genetic-Pareto Prompt Evolution）** 自动优化 SKILL.md / tool descriptions / system prompts / 代码。**No GPU，纯 API 调用，单次 ~$2-10**。

## Pipeline（7 步）

```
read current SKILL/prompt/tool
   ↓
Generate eval dataset (DSPy)
   ↓
GEPA Optimizer ← execution traces（失败的 *为什么*，不只是失败）
   ↓
Candidate variants
   ↓
Constraint gates:
  1. Full test suite pass 100%
  2. Size limit (SKILL ≤15KB, tool desc ≤500ch)
  3. Caching compatibility（无 mid-conversation 变更）
  4. Semantic preservation（不漂移）
  5. PR review（人审，永不直 commit）
   ↓
Best variant → PR against hermes-agent
```

## 5 阶段路线

| Phase | Target | Engine | Status |
|-------|--------|--------|--------|
| 1 | SKILL.md 文件 | DSPy+GEPA | ✅ Implemented |
| 2 | Tool descriptions | DSPy+GEPA | 🔲 Planned |
| 3 | System prompt sections | DSPy+GEPA | 🔲 Planned |
| 4 | Tool implementation code | Darwinian Evolver (AGPL) | 🔲 Planned |
| 5 | Continuous improvement loop | Automated pipeline | 🔲 Planned |

## 安装 + 跑（标准 4 步）

```bash
# 1. 克隆（Mac mini 24GB 跑得动，clone --depth=1 省 90% 空间）
git clone --depth=1 https://github.com/NousResearch/hermes-agent-self-evolution.git /tmp/self-evo
cd /tmp/self-evo && pip install -e ".[dev]"

# 2. 指向 Hermes skill 目录
export HERMES_AGENT_REPO=~/.hermes   # 注意是 .hermes 根，不是 skills/

# 3. 用合成 eval 试水（最快）
python -m evolution.skills.evolve_skill \
    --skill hermes-see-act \
    --iterations 10 \
    --eval-source synthetic

# 4. 用真实 session history（更准）
python -m evolution.skills.evolve_skill \
    --skill hermes-see-act \
    --iterations 10 \
    --eval-source sessiondb
```

## eval-source sessiondb 三大特性

1. **自动挖真实历史**：从 `~/.claude/history.jsonl`（Claude Code）+ `~/.copilot/session-state/*/events.jsonl`（Copilot）+ Hermes state.db 拉真实工具调用
2. **两级过滤**：cheap keyword heuristic pre-filter → LLM-as-judge via DSPy（节省 80% LLM 调用）
3. **Secret detection**：自动剔除 API key/token/PII，防止污染 eval data
4. **109 tests** 覆盖（secret detect / importer / 两级 filter）

## 适用判断：什么 skill 该跑 GEPA？

| 信号 | 是否跑 GEPA |
|------|------|
| skill 失败率 > 20%（cron log 里频繁 retry） | ✅ 必跑 |
| skill 体积 < 5KB + 流程稳定 + 高频用 | ❌ 性价比低 |
| skill 描述不清导致 agent 不知道何时触发 | ✅ 优化 description |
| 跨平台/跨渠道 SOP 类的 skill（如 channel-universal-sop） | ⚠️ 慎跑，semantic preservation 难 |
| 自创 skill 跑过 < 5 次 | ❌ eval 数据不足，结果不可信 |

## 与手动优化的对比

| 维度 | 手动 patch | GEPA |
|------|-----------|------|
| 成本 | $0（已用 LLM） | $2-10/run |
| 速度 | 几分钟 | 30min-2h（取决于 iterations） |
| 客观性 | 主观 | LLM-as-judge 多维 rubric |
| 适用 | 已知具体问题 | "这 skill 整体可以更好" |
| 风险 | patch 错就坏 | constraint gates 兜底 |

## 已知局限

- **P2-P5 未实现**：tool descriptions / prompt sections / code / continuous loop 都还 planned，**别指望一键优化全部**
- **AGPL 风险**：Phase 4 用 Darwinian Evolver (AGPL v3)，仅作 external CLI 调用，避免传染 Hermes (MIT)
- **ICLR Oral 但学术评测为主**：生产使用前建议先 synthetic 跑 + 人审 best variant PR
- **Mac mini 24GB OK**：DSPy+GEPA 是 LLM API 调用，pipeline 自身 < 200MB 内存

## 关联资源

- 官方 README: github.com/NousResearch/hermes-agent-self-evolution/blob/master/README.md
- 完整架构 PLAN.md（5 阶段详细设计）
- ICLR 2026 论文 arxiv.org/abs/2507.19457（GEPA 原始论文）
- 官方 showcase: gepa-ai.github.io/gepa/guides/use-cases/（Nous Hermes 案例）