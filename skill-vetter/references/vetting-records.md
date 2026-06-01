# External Tool Vetting Records

## LG-token-saver (jnbno1163/LG-token-saver)

**Status**: Repo exists (6 stars, 2 commits, 2026-06-01)  
**Relevance to Hermes**: ❌ Claude Code场景的工具，不适用于Hermes Agent  
**Install command**: FAKE — `npx skills add jnbno1163/LG-token-saver` is invalid (npx has no `skills` subcommand)  
**Risk**: 🟢 LOW (not malicious, just not for Hermes)  
**Verdict**: 不需要安装。Claude Code用户可参考其token优化思路（输入过滤+输出压缩+上下文管理），但Hermes不适用。

---

## EverMe (EverMind-AI/EverMe)

**Status**: Repo exists (4 stars, 5 commits, 3 days old as of 2026-06-02)  
**Relevance to Hermes**: ✅ 明确支持Hermes的跨Agent记忆工具  
**Description**: 跨会话/跨代码/跨Agent记忆互通，CLI + Agent插件套件  
**Supported platforms**: mcp, cursor, hermes, codex, evermind  
**License**: Apache-2.0  
**Risk**: 🟡 MEDIUM (very new, 5 commits, limited history)  
**Verdict**: 值得关注，但需要深入评估是否与现有Hindsight记忆层冲突，以及集成成本。  
**Repo**: https://github.com/EverMind-AI/EverMe  
**Note**: 视频里提到的"EverMe C端产品"是EverMind付费产品，GitHub上是开源核心。

---

## Vetting Lessons (2026-06-02)

- `mcp_github_get_file_contents` 返回404不代表仓库不存在（通道差异）
- `browser_navigate` 到 github.com 能成功时用GitHub站内搜索
- SearXNG (web_search) 502时，用 `browser_navigate` 到 GitHub search 作为fallback
- MCP chrome bridge 持续断连时，browser_navigate 是稳定的备选
