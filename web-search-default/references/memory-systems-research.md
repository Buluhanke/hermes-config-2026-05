# AI Agent 长期记忆系统研究（2026-07）

## 核心问题
现有 MEMORY.md + fact_store 存在字符限制（2200/6600）和语义缺失，skill 不是沉淀流程的工具。

## 2026年最新方案对比

| 方案 | Stars | 特点 | 状态 |
|------|------|------|------|
| **Mnemosyne** (mnemosyne-oss) | 1.3k | Hermes-first, 零依赖SQLite, v3.10.1, 40 contributors | ⭐首推 |
| **Mem0** | — | benchmark 92.5 LoCoMo / 94.4 LongMemEval, 21框架集成 | 重量级 |
| **MAGMA** | — | ACL 2026, Multi-Graph Memory Architecture | 学术前沿 |
| **Continuum Memory (CMA)** | — | arXiv, 持久状态+时序链+语义抽象 | 学术 |
| **Hermes FTS5 Semantic Skill** | — | Issue #17649, 官方开发中 | 待上线 |

## Mnemosyne 详情
- 官网: mnemosyne.site
- 安装: `pip install mnemosyne-memory`
- GitHub: github.com/AxDSan/Mnemosyne
- 特性: SQLite-backed, sub-millisecond, Hermes原生
- 2026-06-22 最新 v3.10.1

## 关键论文
- Continuum Memory Architectures: arxiv.org/pdf/2601.09913v1
- Is Agent Memory a Database?: arxiv.org/html/2605.26252v1
- MAGMA: aclanthology.org/2026.acl-long.1709.pdf
- Anatomy of Agentic Memory: arxiv.org/pdf/2602.19320v1

## 落地建议
**立即安装 Mnemosyne**：`pip install mnemosyne-memory`，替换现有 MEMORY.md + fact_store 方案。
