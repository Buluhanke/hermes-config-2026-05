# LLM Wiki 参考资料

## 原始来源

### Karpathy LLM Wiki Gist
**地址**：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
**星标**：5k+，作者：Andrej Karpathy

核心摘录：
> "Instead of just retrieving from raw documents at query time, the LLM incrementally builds and maintains a persistent wiki — a structured, interlinked collection of markdown files that sits between you and the raw sources."

> "The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. LLMs don't get bored, don't forget cross-references, can touch 15 files in one pass."

> "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."

**分工**：
- 人类：筛选来源、引导分析方向、问好问题、思考意义
- LLM：读取、总结、编写、更新、交叉引用

---

### nashsu/llm_wiki（完整实现）
**地址**：https://github.com/nashsu/llm_wiki
**星标**：7.6k，GPL-3.0，Tauri 桌面应用

**完整功能清单**：
- Two-step chain-of-thought ingest（分析→生成两段式）
- SHA256 增量缓存
- 4-signal knowledge graph（4信号知识图谱评分）
- Louvain 社区发现
- 多格式文档支持（PDF/DOCX/PPTX/XLSX/图片）
- Deep Research（联网搜索+自动摄入）
- Chrome Web Clipper 扩展
- Obsidian 兼容
- 多 LLM 支持（OpenAI/Anthropic/Google/Ollama）

**技术栈**：Rust 69% + TypeScript，Tauri v2 桌面，React 19 前端

---

### OpenHuman（参考项目）
**地址**：https://github.com/tinyhumansai/openhuman
**星标**：9.8k，GPL-3.0

**Auto-fetch 设计**（对 Hermes 有参考价值）：
- 118+ OAuth 平台一键接入
- 20分钟自动同步循环
- Memory Tree 压缩（≤3k token Markdown 块存 SQLite）
- TokenJuice 智能压缩（减少80% token消耗）

**Hermes 可借鉴**：Auto-fetch 的"定期自动采集数据到本地"思路，不需要实时，但定期同步。

---

### VoxCPM2（语音升级备选）
**地址**：https://github.com/OpenBMB/VoxCPM
**星标**：18.9k，Apache-2.0

- 2B 参数，48kHz，30种语言+9种中文方言
- Voice Design（自然语言描述生成音色）
- Ultimate Cloning（参考音频+Transcript 完美克隆）
- 需要 NVIDIA GPU（Mac mini 不可用）
- **升级条件**：有 GPU 服务器后可用 nano-vLLM 部署

---

## 关键结论

| 项目 | 对 Hermes | 可用性 |
|------|---------|-------|
| Karpathy LLM Wiki 理念 | ✅ 直接适用 | ✅ 立即可用 |
| nashsu/llm_wiki 实现 | 参考架构 | 桌面应用，Mac mini 无显示器不适用 |
| OpenHuman Auto-fetch | 参考设计 | 可借鉴到 Hermes cronjob |
| VoxCPM2 TTS | 未来升级 | 需 GPU 服务器 |
