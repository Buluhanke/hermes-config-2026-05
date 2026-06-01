# Direction D 执行层分析 — 2026-06-02

## DRY_RUN Precondition 6项评估结果

| # | 条件 | 结果 | 数据来源 |
|---|------|------|---------|
| ① | 业务场景稳定性 | ❌ FAIL | 仅1次browser（06-01全天），远<5次/小时 |
| ② | wininfo噪音 | ✅ FIXED | handler修复后零wininfo误报 |
| ③ | RPA脚本路径 | ✅ PASS | 14KB, `/Users/aimac/.hermes/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py` |
| ④ | 夜间误触发 | ✅ PASS | 230次深夜触发全部→none |
| ⑤ | 日志连续性 | ✅ PASS | 990条dry-run，3+天连续 |
| ⑥ | 回滚方案 | ✅ PASS | 2份备份文件可恢复 |

**结论**：DRY_RUN=False 不成熟。第①项不通过时，即使其他5项全绿，切换后也无实质动作（全部场景映射为"none"）。

## Handler Whitelist 修复验证

**备份对比（3版本）**：

| 版本 | other | unknown | desktop | browser | 修改时间 |
|------|-------|---------|---------|---------|---------|
| bak.0024 | wininfo | wininfo | wininfo | wininfo | 06-01 00:24 |
| bak.0138 | wininfo | wininfo | wininfo | wininfo | 06-01 01:38 |
| 当前 | **none** | **none** | **none** | wininfo | 06-01 06:56 |

**验证方法**：
1. `ls -la handler.py` → 获取修改时间 06:56
2. `grep "DATE" log | grep "wininfo for scene=other" | cut -c2-11 | sort | uniq -c | sort -rn` → 全部在 02:48-02:52
3. `grep "DATE" log | grep -E "0[6-9]:|1[0-9]:" | grep "wininfo for scene=other" | wc -l` → 0（06:00后的异常事件数）
4. 验证通过 ✅

**关键发现**：`awk '/HH:MM:SS/,0'` 在 `grep "DATE"` 的输出管道中可能因为行首格式 `[DATE HH:MM:SS]` 与 awk 的范围匹配不兼容而失效。✅ 替代方案：`grep -E "HH_RANGE:"` 按小时范围过滤更可靠。

## Ollama 白天宕机模式

- 06-01 16:46 起 → 23:07 止，Ollama 因 macOS 内存压力被 force kill
- 后果：全部场景分类降级为"unknown"（handler 返回错误）
- 但 handler 仍正常记录 dry-run
- 与已知的凌晨 crash 模式（02:50-03:10）不同——这是首次白天被 kill
- **影响**：白天用户活跃时段 Ollama 不可用会导致 screen_watcher 无法区分真实场景

## 当日场景分布（06-01）

- other: 369（占比 **~93%**）
- unknown: 17（Ollama crash 期间）
- desktop: 9
- browser: 1（用户唯一一次业务操作）
- 其他(wechat/1688/dingtalk/calculator/telegram): 0

## RPA 动作清单

当前 `hermes_desktop_rpa.py` 支持：
- ocr — 截图+OCR读取屏幕文字
- wininfo — 获取Chrome窗口位置/尺寸/标题
- click x,y — 点击屏幕坐标
- nclick nx,ny — Qwen3-VL归一化坐标(0-1000)转像素点击
- type <文字> — 粘贴文字到当前焦点
- press <键> — 按键 (enter/tab/esc/cmd-空格等)
- openurl <URL> — 在Chrome打开URL
- send <消息> — 在ChatGPT输入并发送
- readchat — 读取ChatGPT回复
- scroll <次数> — 滚动

## 后续建议

1. 维持 DRY_RUN=True，等待业务场景稳定
2. 考虑 screen_watcher 非 cron 环境持续运行时积累场景频率数据
3. 监控 Ollama 白天被 kill 的频率——如果高频发生，需设置自动重启守卫
