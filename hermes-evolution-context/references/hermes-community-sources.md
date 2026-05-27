# Hermes 社区学习资源清单（2026-05-26汇总）

## 核心官方
| 资源 | 地址 | 说明 |
|------|------|------|
| GitHub | https://github.com/nousresearch/hermes-agent | 主仓库，commits/issues/PR |
| 官方文档 | https://hermes-agent.nousresearch.com/docs | 最新文档 |
| Skills Hub | https://hermes-agent.nousresearch.com/docs/zh-Hans/skills | 官方技能库 |

## 社区
| 资源 | 地址 | 说明 |
|------|------|------|
| Discord | https://discord.gg/nousresearch | 10.8万会员，最活跃 |
| Reddit | https://reddit.com/r/hermesagent | 用户真实讨论 |
| X (Twitter) | https://x.com/nousresearch | 官方动态 |
| awesome-hermes-agent | https://github.com/0xNyk/awesome-hermes-agent | 3.4k stars，精选资源 |

## 学习路径
1. 每日03:00 cron 自动抓取 GitHub commits + issues
2. 遇到问题先搜 Discord/Reddit，通常有人踩过坑
3. 官方文档是最权威参考，不要依赖记忆

## SOUL.md 与 .hermes.md 的区别
- `~/.hermes/SOUL.md` — HERMES_HOME，全局人格文件，优先级最高
- `~/.hermes/hermes-agent/.hermes.md` — 项目级上下文，优先级次之
- 两者都是官方支持的 context files 机制