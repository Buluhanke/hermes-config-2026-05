# 平台可用性状态追踪

## 2026-08-01 实测

| 平台 | 工具 | 状态 | 备注 |
|------|------|------|------|
| web_search | 通用搜索 | ✅ 骨干 | 最可靠 |
| web_extract | 内容抓取 | ✅ 骨干 | 配合web_search |
| HackerNews | opencli hackernews search | ✅ | 技术讨论，速度快 |
| GitHub | gh CLI | ✅ | repos搜索，无需浏览器 |
| Exa | mcporter call exa.web_search_exa | ❌ | MCP server未配置 |
| Reddit | opencli reddit search | ❌ | 需Browser Bridge，daemon未连接 |
| V2EX | opencli v2ex search | ❌ | 工具未配置 |
| 微博 | opencli weibo search | ❌ | 需Browser Bridge |
| arxiv | opencli arxiv search | ⚠️ | 429限流，直接搜arXiv链接更稳 |
| Dev.to | opencli devto search | ❌ | 命令格式不支持search |
| ProductHunt | opencli producthunt search | ❌ | 命令格式不支持search |

## opencli 平台分类

### 直接可用（无需daemon）
- hackernews: `opencli hackernews search "query" --limit N --format md`
- github: `gh search repos "query" --sort stars --limit N`

### 需 Browser Bridge（daemon + Chrome扩展）
- reddit, v2ex, 微博, twitter, xiaohongshu, bilibili, youtube
- 诊断：`opencli daemon stop && opencli doctor`
- 扩展下载：https://github.com/jackwiner/opencli/releases
