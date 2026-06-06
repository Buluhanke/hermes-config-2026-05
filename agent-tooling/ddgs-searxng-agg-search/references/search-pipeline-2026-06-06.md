# 搜索统一入口上线记录 (2026-06-06)

## 背景
用户在 QQ 机器人上确认了最终路由方案，今天（6月6日晚）落地为 `search.py`。

## 统一入口
```bash
python3 ~/.hermes/scripts/search.py "查询" [N]
```

## 路由确认时间线

| 事件 | 时间 |
|---|---|
| `anysearch` CLI 首次安装 | 2026-05-25 |
| `hermes-config-2026-05` 仓库初始化 | 2026-05-16 |
| `last30days` skill 首次安装 | 2026-06-05 21:08 |
| `last30days` 仓库创建 | 2026-01-23 (mvanhorn/last30days-skill) |
| `search.py` 统一路由上线 | 2026-06-05 ~20:50 |
| 搜索路由 QQ 确认 | 2026-06-05 21:12 |

## 技能与仓库关系

| 技能 | 仓库 | 同步状态 |
|---|---|---|
| `anysearch` | `Buluhanke/hermes-config-2026-05` | origin/main ce32bfa, 2026-06-03 sync |
| `last30days` | `mvanhorn/last30days-skill` | origin/main 26da1e1, local=origin, 同步 |

## Cron 自进化系统

| Job | plist 创建 | 首次日志 | 运行频率 |
|---|---|---|---|
| `ai.hermes.self-evolution` | 2026-05-25 08:54 | 2026-06-04 17:46 | 每30分钟 |
| `ai.hermes.self-evolution-daily` | 2026-06-05 11:46 | — (09:30 每日) | 每日 09:30 |

## 关键规则（QQ确认版）
路由由 Hermes 把关，原则：
- 事实/评测/价格/技术 → `anysearch` 为主 + `last30days` 并联补充
- 舆情/口碑/趋势/过去N天/月 → `last30days` 为主 + `anysearch` 补充
- 模糊地带 → `anysearch` 优先 + `last30days` 同时跑
- `anysearch` 挂了 → `agg_search.py` (ddgs) 兜底

## 已知问题
- `last30days` 中文话题在 HN/Reddit 源数据少（英文话题效果最佳）
- 今日之前 `last30days` 虽装过但未进统一路由，实际未生效
- 搜索系统从今天（6月6日）起才算完整版
