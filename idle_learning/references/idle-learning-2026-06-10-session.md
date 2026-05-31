# Idle Learning 2026-06-10 Session

## 方向 C — 决策操作（screen_watcher 巡检 + 产线验证 + 设计哲学）

### 系统状态快照

| 检查项 | 状态 |
|--------|------|
| screen_watcher 进程 | 已死（上次截图 6/1 00:39，9天 stale）→ **已重启** ✅ |
| Handler lock 残留 | 无 ✅ |
| Ollama 进程 | ✅ 运行中 |
| 本地模型 | qwen2.5:1.5b (0.92GB) + qwen3-vl:2b (1.76GB) |
| 网络 | github:blocked, hn:ok, Firebase API:ok |
| Dry-run 记录 | 618 条（+1 自重启后新增） |
| gateway.log 污染 | 1361 条旧记录，**0 条新增**（hook 压制生效 ✅） |

### Negation Fix 生产验证

**之前（修复前，Jun 1 00:40）**：
```
[2026-06-01 00:40:12] 分析结果: 没有需要处理的内容或异常。
[2026-06-01 00:40:12] [AUTO-EXEC-DRY] Would execute: wininfo for scene=other
[2026-06-01 00:40:12] 处理完成 [urgent]   ← ❌ 误标 urgent
```

**之后（修复后，Jun 1 00:47）**：
```
[2026-06-01 00:47:14] 分析结果: 没有需要处理的内容或异常。
[2026-06-01 00:47:14] [AUTO-EXEC-DRY] Would execute: wininfo for scene=other
[2026-06-01 00:47:14] 处理完成 [silent]   ← ✅ 正确 silent
```

**结论**：CRITICAL_KEYWORDS 否定词检测在 qwen3-vl:2b 分类 + other 场景下正确工作。所有 other/unknown 场景现在正确标记 [silent] 而非 [urgent]。修复已投产验证通过。

### screen_watcher 复活验证清单（2026-06-10 实测版）

当 idle_learning 发现 screen_watcher 已死时，执行以下 6 步验证确保链路完整：

1. **pkill 旧进程** → `pkill -f screen_watcher`（确保旧进程不会掩盖问题）
2. **启动新进程** → `terminal(background=true)` 执行 `python3 ~/.hermes/scripts/screen_watcher.py`
3. **验证进程存活** → `ps aux | grep screen_watcher`（确认 PID 存在）
4. **验证截图更新** → `ls -lt ~/.hermes/screenshots/current.png`（时间戳应在当前分钟）
5. **验证 handler 触发** → `tail -10 ~/.hermes/logs/screen_trigger.log`（应有新 "触发！" 记录）
6. **验证分类与标记正确** → 检查新记录中 scene=other 是否标记 [silent] 而非 [urgent]

完整验证链耗时约 15-20s（截图等待 8s + handler 分析 7-12s）。

### 场景分布快照（618 dry-run 条目）

| 场景 | 数量 | 占比 | 说明 |
|------|------|------|------|
| unknown | 301 | 49% | qwen3-vl:2b 对非典型界面保守 |
| browser | 233 | 38% | 分类准确 |
| desktop | 42 | 7% | 桌面背景分类 |
| other | 33 | 5% | 均已标记 [silent] ✅ |
| wechat | 6 | 1% | |
| calculator | 3 | <1% | |

### "Friction = Focus, Focus = Product" — auto_execute 设计哲学

**来源**：HN [196pts] thoughts.hmmz.org/2026-05-31.html — 一位用 AI 构建 50+ 项目的工程师的反思

**核心论点**：
- AI 移除了创作中的"摩擦"（friction）同时也移除了"承诺"（commitment）
- 无承诺 → 无专注 → 无有意义产出
- 作者将语音笔记转博客的 pipeline 产出是"无节制的垃圾"（unbridled garbage）
- 因为移除了努力，所以移除了投入，所以失去了产出质量

**作者原话**（关键引用）：
> "Quality writing is not conversational English simply cast through a lens: conversational English is low-bit rate noise, quality writing attempts to capture high bit rate information with better formed concepts"

**作者对 AI 工具的批评**：
- "Thermonuclear ADHD amplifier" — AI 放大注意力分散
- "10,000 LOC untested Python/JS mess in 5 minutes helps nobody"
- 所有供应商的激励机制都是反的：更多 tokens = 更多收入

**对 Hermes auto_execute 的启示**：

1. **验证门不可省略**：auto_execute DRY_RUN=False 不能是一个二值开关。需要用 SafeGround 框架的分级置信度机制，在低置信度时 defer 而非执行。

2. **"摩擦"作为质量屏障**：完全无缝的自动执行会产出垃圾。auto_execute 应该保留关键决策点的人工确认（如：高影响操作、涉及金钱/数据的操作）。

3. **Gradient transition over binary switch**：从 DRY_RUN=True → False 应该分阶段：
   - Phase 1: DRY_RUN=True（只记录，不执行）— ✅ 当前状态
   - Phase 2: DRY_RUN=False + 置信度门限（置信度>90% 才执行，强制回退）
   - Phase 3: DRY_RUN=False + 低风险动作白名单（只执行无害动作如 wininfo）
   - Phase 4: 全自动 + 异常熔断（检测到循环/错误模式时自动切回 DRY_RUN）

4. **"The solution might be cancelling my AI subscription"** 的正面解读：最好的自动化不是"做更多"，而是"做更少但更正确"。
