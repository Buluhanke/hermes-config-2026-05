# self_evolution 飞轮首次闭环实战（2026-06-05 W23 周报）

> 配套：`safe-cron-do-segment-v1-1-20260605.md` + `safe-cron-script-edit-protocol-20260605.md`

## 闭环背景

**W23 周报数据**（2026-06-03 02:00 ~ 2026-06-04 22:54）暴露进化飞轮断链：

```
本周 fact 增长:
  error_pattern 17 条 (avg_trust=0.7)   ← 全部自指型废话
  general       6 条 (avg_trust=0.78)
  infrastructure 1 条 (avg_trust=0.85)  ← 唯一实战
  project       2 条 (avg_trust=0.6)
```

`error_pattern` 17 条全是 "小时工具错误聚集: X 次" 这种**描述自己重复出现**的 fact，trust=0.7 没法驱动任何修复动作。**真正能驱动修复的 fact 0 条**。

## 6/5 补的 3 个 Do 段（hourly 模式从 2/5 真修 → 5/5 真修）

| 模式 | 旧行为 | 新行为 | 信任分 |
|---|---|---|---|
| Chrome 9333 异常 | 立刻 pkill+open | **3 次 lsof 健康检查（2s 间隔）→ 失败才重启 + 写 fact 去重** | 0.9 |
| Telegram 错误>5/h + 代理可达 | 写 fact 不修 | **SIGTERM gateway → 5s → SIGKILL 兜底 → 拉起 → 验证 PID** | 0.85 |
| Telegram 错误>3/h + 代理不可达 | 写 fact 等手动 | **自动试拉起 clash/ClashX/v2ray** | 0.9 |

## 6/5 补的 1 个 daily 输出（结构化 JSON）

**根因**：daily 段只写 markdown 笔记（给人读），**没写 JSON 报告**（给程序读）。`self_optimization/report_YYYYMMDD.json` 6/4 缺失。

**修复**：daily 段加第 4 段，每次跑同时输出 JSON 报告，含 `patterns / api_health / disk_pct / today_facts / today_fixes` 字段。

**双轨设计**：
- **Markdown 笔记** → 人读（次日计划 / 人工判断建议）
- **JSON 报告** → 程序读（weekly 阶段 `jq` 汇总）

**6/5 首次产出**：
```json
{
  "time": "2026-06-05 08:02",
  "errors": 12,
  "patterns": {},
  "api_health": {"DeepSeek": "❌ HTTPError", "Telegram": "✅"},
  "searches": [],
  "memory_mb": 24576,
  "disk_pct": 41,
  "today_facts": 0,
  "today_fixes": 0
}
```

## ⚠️ 自指型 fact 检测（关键洞见）

写 fact 时如果发现自己**正在描述自己重复出现**，就是自指型：

| 反面案例 | 为什么是自指 |
|---|---|
| `小时工具错误聚集: 15 次 — 需要 daily 分析分布` | 写 fact 本身不修复，重复 17 次也没真修 |
| `Telegram network error 频繁 (4/h) 且代理 7897 不可达 — 需要手动检查` | "需要手动检查" = 不闭环 |

**正面案例**：
| 案例 | 为什么闭环 |
|---|---|
| `Chrome CDP 9333 端口异常 → 已自动重启 Chrome (3次重试无效)` | "已自动重启" = 动作落地 |
| `Telegram Pool timeout 高发 — 已自动重启 gateway, 检查 HERMES_TELEGRAM_HTTP_POOL_SIZE` | "已自动重启" + 下次行动建议 |

**判断标准**：读 fact 第一行，**有"已... / 已修复 / 已重启"等动作动词**的 = 实战；**有"需要 / 待 / 建议"等占位动词**的 = 自指。

## 3 天后验证（6/8 早 9:00 daily 自动跑）

应该能看到：
- `evolution.log` 出现 `✅ Gateway 重启成功` 或 `✅ Chrome 重启命令已发`（Do 段真触发）
- `infrastructure` 类 fact 从 1 条涨到 5+ 条（实战沉淀）
- `error_pattern` 类从 17 条不再涨（不写自指型）
- `report_20260608.json` `today_fixes > 0`

**未达预期** → 调阈值（TG 错误阈值 5/h 太高，3/h 试）。

## 配套动手清单

下次有人想加 Do 段时**先看本文件 + safe-cron-do-segment-v1-1**，不要直接看老代码"模仿"。

1. 先看 `references/safe-cron-script-edit-protocol-20260605.md`（协议 5 步）
2. 看本文件 + `safe-cron-do-segment-v1-1-20260605.md`（BSD/RSS 等 macOS 特定坑）
3. 看 `macos-process-lifecycle/references/mem-patrol-v1-bug-20260605.md`（v1.0 误杀反例）
4. 静态分析 + 手动 dry-run（不要跳过）
5. 上 launchd 后 30min 内查日志
