# idle-learning-rounds 变体：4步idle学习流

> 从 `SKILL.md` v2.0 移出的独立流程文档。原位置 lines 242-389。

---

## 适用场景

任务驱动型idle学习（用户预先布置"空闲时做X"），与A→B→C→D多方向扫描**不同**。

---

## 标准4步

| Step | 动作 | 工具 | 失败处理 |
|---|---|---|---|
| 1. Search 社区 | 搜官方docs/社区论坛最新讨论找1个有用技巧 | `web_search`(DuckDuckGo)优先, `web_extract`抓官方docs | SearXNG 0返回→立刻换web_search；3次0结果→抓GitHub releases/official docs |
| 2. Install skill | `hermes skills search <kw>`找对应skill，`inspect`看trust/verdict，`install` | `hermes skills install <identifier>` | 首问：这是Hermes内置功能吗？官方docs优先。已装核心skill不重装。找Ponytail rung4已知方案 |
| 2a. 装依赖 | skill装完后 | `uv pip install <pkg>` | 跑完`uv pip list | grep <pkg>`验证 |
| 2b. 验证已装 | --force说already installed时 | `hermes skills list | grep <name>` | 若搜到说明已在库里，直接`skill_view`加载 |
| 3. Ask AI site | `browser_navigate`AI站点提问 | 本地Chrome(`mcp_chrome_devtools_mcp_*`)+SOUL标已登录的(Gemini/Doubao/ChatGPT) | 卡"思考"145s+/撞登录墙→立刻abort，走self-reasoning，不阻塞cron |
| 4. Write MEMORY | 把学到的提炼成结构化条目追加MEMORY.md | `patch`工具追加新日期块 | MEMORY.md超12KB→替换最旧日期块，不新增 |

---

## 高效技巧来源清单（按优先级）

| 优先级 | 来源 | URL | 优势 | 适合找什么 |
|---|---|---|---|---|
| 1 | Hermes官方Tips页 | https://hermes-agent.nousresearch.com/docs/guides/tips/ | SSR, web_extract一次抓到5k字+干货 | 用户效率技巧、CLI快捷操作、配置优化 |
| 2 | NousResearch Discord | discord.gg/nousresearch | 官方社区，版本发布先发这里 | Hermes新功能、skill更新 |
| 3 | GitHub releases | github.com/NousResearch/hermes-agent/releases |  changelog | 版本更新、breaking changes |
| 4 | agentskills.io | agentskills.io | 社区skill市场 | 新工具skill、按需搜索 |
| 5 | HuggingFace Daily | huggingface.co/daily | 每日ML/AI论文精选 | 前沿模型、sota方法 |
| 6 | arXiv cs.AI | arxiv.org/list/cs.AI/recent | AI最新研究 | 论文级技术细节 |
