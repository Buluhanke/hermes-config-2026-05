# Fallback Skills — 每日采集器兜底列表

**最后更新**: 2026-06-26

当 GitHub API 抓取失败时，使用以下已知有效的 skill 名称作为兜底。这些 skill 在 Hermes Official 或 HermesHub 仓库中真实存在，且本地归档目录中大概率有备份。

## 核心兜底技能（按优先级）

### Browser Automation
- `hands-free-browser` — 无头浏览器自动化
- `browser-cdp-control` — CDP 协议直接控制（✅ 2026-06-26 从归档恢复成功）
- `browser-scraper` — 网页抓取专用

### Memory
- `memory-fact-store` — 事实存储管理
- `memory-hpc` — 高性能记忆缓存

### Vision
- `vision-ocr` — OCR 文字识别
- `vision-agent` — 视觉分析代理
- `photo-analysis` — 图片分析

### Self-Evolution
- `agentskills` — 技能市场集成
- `skill-optimizer` — 技能自动优化
- `proactive-execution` — 主动执行机制

### Terminal Control
- `macos-computer-use` — macOS 桌面控制

### Web Scraping
- `web-scraping-advanced` — 高级网页抓取

### DevOps
- `python-packaging` — Python 打包工具

### Communication
- `telegram-mcp` — Telegram MCP 桥接
- `discord-bot` — Discord 机器人集成

## 恢复方法

### 方法 1: 从归档目录恢复（推荐）

```bash
# 查找归档中的技能
find ~/.hermes/skills/.archive -name "SKILL.md" | grep <skill-name>

# 恢复单个技能
mv ~/.hermes/skills/.archive/<category>/<skill-name> ~/.hermes/skills/<category>/
```

### 方法 2: 从官方仓库 clone

```bash
cd ~/.hermes/skills
git clone --depth 1 --sparse https://github.com/NousResearch/hermes-agent.git temp-clone
cd temp-clone
git sparse-checkout set skills/<skill-name>
mv skills/<skill-name> ~/.hermes/skills/
cd ..
rm -rf temp-clone
```

### 方法 3: 使用 hermes CLI

```bash
hermes skills install official/<skill-name>
```

## 已知失败案例

- ❌ `gh api repos/NousResearch/hermes-agent/contents/skills` — 返回空（认证问题）
- ❌ `gh api repos/amanning3390/hermeshub/contents/skills` — 返回空（API 限制）

## 成功提取方法

✅ 使用 `web_search` + `web_extract` 从 GitHub 页面解析：

```python
results = web_search(query="hermes-agent skills list site:github.com/NousResearch")
content = web_extract(urls=[r['url'] for r in results['data']['web'][:3]])
# 解析 content 提取技能名称
```

## 归档目录结构

```
~/.hermes/skills/.archive/
├── agent-tooling/
│   └── browser-cdp-control/
├── computer-use/
│   └── macos-computer-use/
├── vision-ocr/
│   └── photo-analysis/
├── memory/
│   └── fact-store-manager/
└── ...
```

## 每日采集脚本修复记录

### 2026-06-26
- **问题**: `discover_skills_from_sources()` 使用模拟数据生成占位符技能名（skill-1, skill-2），导致 git clone 失败
- **修复**: 
  1. 改为从真实 GitHub repo 列技能目录
  2. 添加 fallback skill 列表兜底
  3. 安装逻辑改为优先从归档目录恢复
  4. 缩短 hermes CLI 超时到 20 秒

### 2026-06-25
- 初始版本使用硬编码模拟数据，未实际抓取