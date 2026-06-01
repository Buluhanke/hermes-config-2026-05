# Horizon — 中文日报快速参考

部署位置: `~/dev/Horizon/`
入口: `uv run horizon` (定义在 `pyproject.toml` → `[project.scripts]` → `horizon = "src.main:main"`)
工作目录: `~/dev/Horizon/`

## Config 关键字段

| 字段 | 路径 | 值 |
|------|------|----|
| 语言 | `ai.languages` | `["zh"]` |
| 模型 | `ai.provider` + `ai.model` | `deepseek` + `deepseek-chat` |
| API Key | `ai.api_key_env` | `DEEPSEEK_API_KEY` |
| 评分阈值 | `filtering.ai_score_threshold` | 6.0 (6/10分以上才入选) |
| 时间窗口 | `filtering.time_window_hours` | 24 |

完整配置文件: `~/dev/Horizon/data/config.json`
环境变量文件: `~/dev/Horizon/.env`

## 输出文件

```
data/summaries/horizon-YYYY-MM-DD-zh.md    ← 主输出（中文）
docs/_posts/YYYY-MM-DD-summary-zh.md       ← GitHub Pages 副本
```

## 命令速查

```bash
# 运行一次日报
cd ~/dev/Horizon && uv run horizon

# CLI 测试 webhook 推送
uv run horizon-webhook --dry-run --lang zh

# 启动 MCP 服务
uv run horizon-mcp

# 交互式配置向导
uv run horizon-wizard
```

## 已知行为

- 每次运行抓取 HackerNews 前10条 + 已配置的 RSS feeds
- AI 评分过滤: 低于 `ai_score_threshold` (默认6.0) 的丢弃
- 保留的条目会进行 **背景知识丰富** (enrichment) — LLM 补充背景、参考链接、社区讨论
- Token 消耗约 28K/次 (DeepSeek)
- 某些 RSS feed（如 Simon Willison）偶发空错误，不影响其它源
- Telegram 源默认关闭，需要配置 Telegram API 才能启用

## 2026-06-01 首次运行实测

- 输入: 9条 (HackerNews 9 + RSS 0)
- 过滤: 6条 ≥ 6.0
- 丰富: 全部6条
- Token: 28,418 (输入 23,049 + 输出 5,369)
- 耗时: ~3分钟
- 输出质量: 8.0分头条 (Meta AI 提示注入攻破 2FA)
