# DRY_RUN=False Readiness — 2026-06-01 R2 评估

**来源**：2026-06-01 03:50 cron idle_learning 方向C

**生产数据快照（June 1 02:00-03:00）**：
- screen_watcher PID 8748（1:27AM 启动）
- Ollama: qwen3-vl:2b (1.76GB) + qwen2.5:1.5b (0.92GB), num_ctx=1024/4096
- 场景分类：100% "other"（0% unknown），稳定运行
- 否定检测：持续生效，所有 "没有需要处理的内容或异常" 标记 [silent]
- 网络：github:ok, hn:blocked

## 6 条件评估（2026-06-01 R2）

| # | 条件 | 2026-06-01 R2 | 对比 R1 |
|---|------|--------------|---------|
| ① 基线数据 | ✅ 730 ≥ 500 | 同 |
| ② Ollama 稳定性 | ✅ June 1 起 0% unknown | 同（日期分片后通过） |
| ③ 动作多样性 | ❌ 1 种（全部 wininfo） | **发现分水岭**：scene 多样 ≠ action 多样 |
| ④ 坐标映射链 | ❌ normalized_click 不存在 | 同 |
| ⑤ SafeGround 置信度 | ❌ 无多采样 | 同 |
| ⑥ 动作分级 | ❌ 全部平坦 | **发现核心瓶颈** |

## 关键发现：ACTION_WHITELIST 平坦化

所有 9 个场景映射到同一个 ("wininfo", None) 动作：
```python
ACTION_WHITELIST = {
    "browser": ("wininfo", None),
    "wechat": ("wininfo", None),
    "1688": ("wininfo", None),
    "dingtalk": ("wininfo", None),
    "telegram": ("wininfo", None),
    "desktop": ("wininfo", None),
    "calculator": ("wininfo", None),
    "other": ("wininfo", None),
    "unknown": ("wininfo", None),
}
```

结果：730 条 dry-run 全部相同，条件③永远无法满足。

**修复方向**：
- idle 场景（other/desktop/calculator/unknown）→ ("none", None)
- 业务场景（browser/wechat/1688）→ 保留 ("wininfo", None)
- 之后才能讨论 Silent/Logged/Confirmed/Blocked 分级

## Handler 健康指标（June 1 凌晨）

- 完整处理周期：~60s（含 60s 冷却 = 2 分钟/次）
- 场景分类耗时：~4-5s（qwen3-vl:2b, resize 400px, num_ctx=1024）
- 凌晨效率：02:00-03:00 约 30 次触发，全部正确 silent
- 无 lock 残留、无超时、无 unknown
