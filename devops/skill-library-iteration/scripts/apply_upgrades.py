#!/usr/bin/env python3
# 把全网调研得到的 2026 更优方案追加进对应 skill 的 SKILL.md。
import os

SK = os.path.expanduser("~/.hermes/skills")

# skill -> 追加的「更优方案」章节
UPGRADES = {
    "audiocraft": """
## 2026 更优方案（全网调研 2026-08 迭代）
原 Audiocraft(MusicGen) 已偏旧。开源音乐生成 SOTA 替代，本地可跑、质量接近 Suno：
- ACE-Step 1.5 — https://github.com/fspecii/ace-step-ui （本地无限、Suno 级，首选）
- YuE — https://github.com/multimodal-art-projection/YuE/ （开源整曲生成）
- SongGeneration / LeVo2 — https://github.com/tencent-ailab/SongGeneration （腾讯高质量整曲）
保留 Audiocraft 作轻量兜底，新任务优先 ACE-Step / YuE。
""",
    "ocr-and-documents": """
## 2026 更优方案（全网调研 2026-08 迭代）
PDF 解析 SOTA（VLM 路线，优于纯 marker/pymupdf）：
- MinerU、olmOCR、Docling —— 复杂版面/公式/表格首选
表格提取：gmft（轻量高性能）、camelot、pdfplumber
保留 pymupdf+marker-pdf 作快速兜底；复杂文档切 MinerU/olmOCR。
""",
    "deep-research": """
## 2026 更优方案（全网调研 2026-08 迭代）
开源 deep research 框架 SOTA，可直接复用其 agent loop：
- gpt-researcher — https://github.com/assafelovic/gpt-researcher (29k★)
- langchain-ai/open_deep_research — https://github.com/langchain-ai/open_deep_research
本技能的多阶段流程与之一致，可叠加使用以省 token。
""",
    "litreview": """
## 2026 更优方案（全网调研 2026-08 迭代）
文献综述 agent SOTA：
- thoth — https://github.com/ahmedeid1/thoth （8 阶段 LangGraph + cite_check 逐条引用核验）
- ResearchPilot — https://github.com/peng1z/ResearchPilot
- LiRA — AAAI 多智能体可靠文献综述框架
优先 thoth 做带引用核验的综述。
""",
    "prometheus-monitoring": """
## 2026 更优方案（全网调研 2026-08 迭代）
VictoriaMetrics 是 Prometheus 的 drop-in 替代：资源占用更低、基数更高、长期存储更省。
大规模/长期监控首选 VM；小规模仍可用 Prometheus。
参考：https://victoriametrics.com/
""",
    "hermes-skills-management": """
## 2026 更优方案（全网调研 2026-08 迭代）
Hermes v0.12.0 官方已内置 Curator（aux model 后台自动巡检/整理 skill 库、淘汰失效技能），可替代部分手工固化。
备份：Dicklesworthstone/agent_settings_backup_script（git 版本化、按大小轮转、易恢复）。
参考：https://github.com/NousResearch/hermes-agent （Curator PR #17277）
""",
    "self-maintenance": """
## 2026 更优方案（全网调研 2026-08 迭代）
Hermes v0.12.0 官方 Curator 已支持后台自主 skill 维护，可接管周期性巡检。
备份恢复用 git 版本化方案：Dicklesworthstone/agent_settings_backup_script。
""",
    "cron-job-reliability": """
## 2026 更优方案（全网调研 2026-08 迭代）
silentwatch-mcp — https://github.com/temurkhan13/silentwatch-mcp
捕获 cron 的"exit-0 但空输出"静默失败、重试风暴、action-budget 泄漏，比单纯监控退出码更可靠。
""",
    "llama-cpp": """
## 2026 更优方案（Apple Silicon，全网调研 2026-08 迭代）
MLX 原生推理在 M 系列最快（M5 Max Llama70B Q4 约 85 tok/s），Ollama 仅慢 4% 但更简单。
Apple Silicon 本地推理优先 MLX（mlx-lm）；大批量/多 GPU 用 vLLM；llama.cpp 仍作跨平台兜底。
""",
    "ollama": """
## 2026 更优方案（Apple Silicon，全网调研 2026-08 迭代）
Apple Silicon 上 MLX 原生比 Ollama 更快（M5 Max 约 85 tok/s）。日常简单用 Ollama 足够；
追求速度切 MLX（mlx-lm）；服务端多卡用 vLLM。
""",
    "memory-cn": """
## 2026 更优方案（全网调研 2026-08 迭代）
Agent 记忆 SOTA：Zep Graphiti（LongMemEval 63.8% vs Mem0 49%）、sqlite-graphrag（单 SQLite 本地图记忆）。
知识图谱型记忆优于纯向量/FTS5，需要做关系推理时优先 Graphiti 类方案。
参考：https://github.com/microsoft/acon （ACON 上下文压缩）
""",
    "manim-video": """
## 2026 更优方案（全网调研 2026-08 迭代）
通用文/图生视频：Wan2.2 / Wan2.7（Apache-2.0，ComfyUI 可用）质量媲美 Sora/Veo，优于老式方案。
数学/算法动画仍用 Manim；通用视频生成切 Wan via ComfyUI。
""",
    "docx": """
## 2026 更优方案（全网调研 2026-08 迭代）
统一 Office 生成：documind SDK（PPTX/DOCX/XLSX/MD 一体化，Apache-2.0）—— https://pypi.org/project/documind/
可替代分散的多个 minimax-docx/pdf/xlsx 库，单一依赖更省心。
""",
    "xlsx": """
## 2026 更优方案（全网调研 2026-08 迭代）
统一 Office 生成：documind SDK（PPTX/DOCX/XLSX/MD 一体化，Apache-2.0）—— https://pypi.org/project/documind/
可替代分散的多个 minimax-xlsx 等库。
""",
    "pdf": """
## 2026 更优方案（全网调研 2026-08 迭代）
PDF 解析 SOTA：MinerU、olmOCR、Docling（VLM 路线）优于传统 pymupdf 文本层。
表格提取：gmft、camelot、pdfplumber。生成类保留本技能。
""",
    "powerpoint": """
## 2026 更优方案（全网调研 2026-08 迭代）
统一 Office 生成：documind SDK（PPTX/DOCX/XLSX/MD 一体化，Apache-2.0）—— https://pypi.org/project/documind/
可替代分散的多个生成库。
""",
    "1688-search-cn-gb-region-skill": """
## 2026 更优方案参考（全网调研 2026-08）
第三方 1688-cli（superjack2050, MIT）复用真实 Chrome 登录态、输出结构化 JSON，可作补充；
但本机以 CDP 后台 Chrome + mtop skuMapOriginal 监听为主（零风控、零焦点抢），不替换。
官方 API 仍须企业资质；MTop 签名难度 4/5，本机无住宅代理不通；付费爬虫(ShopAPIS/HioBuy)需花钱。
""",
    "browser-read-funnel": """
## 2026 更优方案参考（全网调研 2026-08）
真实 Chrome 非无头自动化 SOTA：Quay(CDP+AX树)、Eyebrowse(MCP)、pi-browser-harness。
与本技能「前台真实 Chrome AX 树」思路一致，保留 defuddle/trafilatura 提取。
""",
    "spec-driven-development": """
## 2026 更优方案参考（全网调研 2026-08）
TDD 强制工具：tdd-ai、karajan-code(22 角色 + TDD + SonarQube)、SAM(自主 TDD)。
Claude Code 高级模式：CLAUDE.md + Hooks + 并行子代理，与本技能一致可叠加。
""",
    "test-driven-development": """
## 2026 更优方案参考（全网调研 2026-08）
强制 AI agent TDD 工具：tdd-ai、karajan-code、SAM(autonomous TDD for Claude Code)。
可挂 pre-commit / CI 强制红绿循环。
""",
    "subagent-driven-development": """
## 2026 更优方案参考（全网调研 2026-08）
并行子代理编排：LangChain dynamic subagents、OpenHands delegation、AOrchestra(arXiv:2602.03786)。
本 Hermes delegate_task 已等价，可叠加上述框架思路。
""",
}

applied, skipped = [], []
for name, block in UPGRADES.items():
    path = os.path.join(SK, name, "SKILL.md")
    if not os.path.exists(path):
        skipped.append(f"{name} (no SKILL.md)")
        continue
    with open(path, encoding="utf-8", errors="ignore") as f:
        cur = f.read()
    if "## 2026 更优方案" in cur:
        skipped.append(f"{name} (already patched)")
        continue
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + block)
    applied.append(name)

print("APPLIED:", len(applied))
for a in applied: print("  +", a)
print("SKIPPED:", len(skipped))
for s in skipped: print("  -", s)
