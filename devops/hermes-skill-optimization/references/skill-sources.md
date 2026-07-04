# Top Skills 来源与排名（2026-06-26 验证）

## 数据源

1. **Hermes Atlas Top Skills** — https://hermesatlas.com/lists/top-skills
2. **官方 Bundled Skills Catalog** — https://hermes-agent.nousresearch.com/docs/reference/skills-catalog
3. **Tech Jacks Solutions Top 10** — https://techjacksolutions.com/ai-tools/hermes/best-hermes-skills/
4. **GitHub 搜索** — "hermes agent skills 2026 top popular"

## Top 社区技能排行榜（按 GitHub Stars）

| 排名 | 项目 | Stars | 描述 | 安装优先级 |
|------|------|-------|------|-----------|
| 01 | nexu-io / open-design | 70.8K | Local-first 设计系统，259+ 技能，142+ 设计系统 | ⚠️ 过大，不装 |
| 02 | mukul975 / Anthropic-Cybersecurity-Skills | 20.7K | 817 个网络安全技能，映射 MITRE ATT&CK/NIST CSF 2.0 | ✅ **P0 必装** |
| 03 | Agents365-ai / drawio-skill | 4.6K | 自然语言生成 draw.io 图表，6 种预设 | ✅ **P0 必装** |
| 04 | AMAP-ML / SkillClaw | 2.0K | 技能集体进化，自动去重 + 质量提升 | ✅ **P0 必装** |
| 05 | conorbronsdon / avoid-ai-writing | 2.0K | 去除 AI 写作模式，2 次重写 | ✅ **P1 安装** |
| 09 | ZeroPointRepo / youtube-skills | 291 | YouTube 转录 API，搜索/频道浏览 | ✅ **P1 安装** |
| 11 | Cranot / super-hermes | 256 | 教 Hermes 自己写分析 prompt | ✅ **P1 安装** |
| 26 | Sahil-SS9 / hermes-simplify-swarm | 7 | 多 agent 代码简化（卫生/清晰/正确） | ✅ **P1 安装** |
| 27 | willingning-coder / eagle-eye | 3 | 5 层智能技能检索（FTS5+ 嵌入+RRF） | ✅ **P2 安装** |

## 官方 Bundled Skills 核心类别

### 必恢复（已验证高频使用）

**GitHub 工作流** (6 个): github-issues, github-pr-workflow, github-auth, github-code-review, github-repo-management, codebase-inspection

**软件开发** (9 个): systematic-debugging, test-driven-development, requesting-code-review, simplify-code, hermes-agent-skill-authoring, python-debugpy, node-inspect-debugger, plan, spike

**MLOps** (5 个): jupyter-live-kernel, llama-cpp, huggingface-hub, weights-and-biases, audiocraft-audio-generation

**研究** (3 个): arxiv, llm-wiki, blogwatcher

**工具** (5 个): openhue, powerpoint, xurl, computer-use, teams-meeting-pipeline

## 删除决策记录 (2026-06-26)

**已删除 51 个技能**:
- Creative (20 个): ascii-art/comfyui/manim-video/p5js/excalidraw — 非核心需求
- Productivity (7 个): notion/obsidian/airtable/google-workspace — 用户不用这些平台
- Research (4 个): polymarket/hermes-community-patrol — 功能重叠/不常用
- MLOps (3 个): evaluating-llms-harness/serving-llms-vllm/segment-anything-model — 本地不跑 ML 训练
- Media (3 个): gif-search/songsee/heartmula — 娱乐类，非生产力
- Meta (3 个): hermes-troubleshooting/no-clarifying-questions/verification-before-reporting — 已内化到行为准则

**误删已恢复** (14 个): GitHub 全套 (6) + 软件开发 (5) + 研究 (3)

## 验证命令

```bash
ls -1 ~/.hermes/skills/ | grep -v '^\.' | wc -l  # 期望：~31
ls -1 ~/.hermes/skills/cybersecurity-pack/skills/ | wc -l  # 期望：817
```

---

**最后更新**: 2026-06-26 | **总技能**: 31 目录 +817 网络安全=848 个