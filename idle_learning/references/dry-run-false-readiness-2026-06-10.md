# DRY_RUN=False 切换准备条件（2026-06-10 调研）

## 背景

当前 `screen_trigger_handler.py` 中 `DRY_RUN = True`（line 33），所有 ACTION_WHITELIST 场景仅映射到 `("wininfo", None)` — 非破坏性信息采集。切换到 DRY_RUN=False 需要满足 6 个前置条件。

## 前置条件清单

### 条件 1：动作执行就绪度 — ✅ RPA 脚本就绪

`hermes_desktop_rpa.py` 已支持完整动作集：

| 动作 | 命令格式 | 状态 |
|------|---------|------|
| click | `python3 hermes_desktop_rpa.py click 960,860` | ✅ 基于 cliclick |
| type | `python3 hermes_desktop_rpa.py type "text"` | ✅ 基于 pbcopy + cmd+v |
| press | `python3 hermes_desktop_rpa.py press enter` | ✅ |
| scroll | `python3 hermes_desktop_rpa.py scroll -3` | ✅ |
| openurl | `python3 hermes_desktop_rpa.py openurl https://...` | ✅ （激活 Chrome） |
| wininfo | `python3 hermes_desktop_rpa.py wininfo` | ✅ |
| send | `python3 hermes_desktop_rpa.py send "message"` | ✅ ChatGPT 专用 |
| readchat | `python3 hermes_desktop_rpa.py readchat` | ✅ |
| ocr | `python3 hermes_desktop_rpa.py ocr` | ✅ 截屏+OCR |

**限制**：坐标参数为**像素绝对坐标**（1920×1080 屏幕空间）。cliclick 只能接受整数坐标。

### 条件 2：坐标映射 — ⏳ 待实现

Qwen3-VL 输出 [x, y] 基于 **1000×1000 相对坐标网格**（GitHub #1560 确认）：

```
像素映射公式：
  x_px = int(nx * screen_width / 1000)
  y_px = int(ny * screen_height / 1000)
```

- Qwen3-VL 输出范围 [0, 999]（arXiv 2604.07831 确认）
- cliclick 需要整数像素坐标
- 需要新增 `hermes_desktop_rpa.py` 函数：`normalized_click(nx, ny, sw=1920, sh=1080)`

**⚠️ 已知 grounding 质量问题**（GitHub #1576）：
- 有人报告 Qwen3-VL grounding 性能差，坐标格式错误
- 同一 prompt 多次采样可能输出不同坐标范围
- 建议结合 SafeGround 多采样 + UCOM 异常值检测

### 条件 3：VLM 输出结构化动作 — ❌ 待实现

当前 handler 仅做场景分类（browser/desktop/other），不做 grounding。

需要新增 grounding prompt：

```
"Return a structured JSON list of interactive UI elements with their 
1000×1000 normalized coordinates and actions (click/type/scroll)."
```

参考 Qwen3-VL 官方 system prompt（GitHub #1521）：
- 使用 "screen resolution: 1000×1000" 引导坐标空间
- 不需要传入实际设备分辨率

### 条件 4：不确定性校准（SafeGround 框架）— ❌ 待实现

**SafeGround**（UCSB AI, Feb 2026）为 DRY_RUN=False 提供理论框架：

**核心流程**：
1. **多采样**：同一 prompt 对 qwen3-vl:2b 采样 5-10 次
2. **空间密度图**：将采样坐标投影到离散化屏幕网格
3. **UCOM 三指标组合**：
   - Top-candidate ambiguity：局部混淆（"两个按钮看起来都对"）
   - Information entropy：全局分散（"信念到处扩散"）
   - Concentration deficit：缺乏主导区域（"没有清晰的赢家"）
4. **Learn-Then-Test 校准**：用 Clopper-Pearson 置信界计算 FDR 上限
5. **推理时决策**：UCOM ≤ τ → 执行；UCOM > τ → 弃权/升级

**级联提升效果**（ScreenSpot-Pro 基准）：
- Holo1.5-7B + SafeGround: +5.38pp
- UI-TARS-1.5-7B + SafeGround: +13.12pp

**落地估算**：5 次采样 × 7-24s/次 ≈ 35-120s 额外延迟。

### 条件 5：Confidence-Gated Takeover Handshakes（curvelabs.org）

2026 协议，三层防护：
1. **Step-level confidence gating**：每步动作前检查 UCOM
2. **Takeover handshake**：UCOM 超标时展示执行预览，请求确认
3. **Emotionally legible intent preview**：LLM 生成动作描述（"即将点击 确认付款 按钮"）

### 条件 6：五层 Guardrail 框架（bswen.com）

| 层 | 名称 | Hermes 当前状态 |
|----|------|----------------|
| 1 | Dry-run with previews | ✅ DRY_RUN=True 已实现 |
| 2 | Scoped permissions | ⚠️ ACTION_WHITELIST 已实现但全部是 wininfo |
| 3 | Git-based rollback | ❌ 需实现 checkpoint 创建 |
| 4 | Monitoring & anomaly detection | ✅ screen_trigger.log 已记录 |
| 5 | Human checkpoint | ⚠️ 需设计梯度过渡 |

**"Friction=Focus" 设计哲学**（HN 212pts）：
- 完全移除人类验证环不是目标
- DRY_RUN=True → False 需要**梯度过渡**（非开关切换）
- SafeGround 不确定性分数正好提供自然梯度：DRY_RUN=True → low-confidence auto → high-confidence auto

## 优先级排序

| 优先级 | 条件 | 当前状态 | 工时估算 |
|--------|------|---------|---------|
| P0 | 坐标映射（normalized_click） | ⏳ 待实现 | ~15行代码 |
| P0 | grounding prompt | ❌ 待实现 | prompt 设计 |
| P1 | SafeGround 轻量级实现 | ❌ 待实现 | ~50行代码 + 校准集 |
| P2 | 场景差异化超时 | ⚠️ 已知问题 | ~5行代码改 timeout |
| P2 | 冷却机制加固 | ⚠️ 已知问题 | ~10行代码 |
| P3 | Git checkpoint 回滚 | ❌ | 依赖 git init |
| P3 | 人工验证梯度过渡 | ❌ | 设计阶段 |

## 当前不急于切换的原因

1. 所有 ACTION_WHITELIST 当前仅映射到 wininfo — 切换到 DRY_RUN=False 也不会产生实际动作
2. Qwen3-VL grounding 质量不稳定（GitHub #1576 确认）
3. 缺乏不确定性校准层（SafeGround 未集成）
4. "Friction=Focus" 设计哲学要求 gradient 过渡

## 新增发现：handler lock 非残留

**New insight from 2026-06-10 R2 session**：
- handler_lock 文件存在 ≠ handler 已死
- 实测：lock 文件 timestamp 00:51，PID 4344 `screen_trigger_handler.py` 实际在运行
- 之前几个 session 假设 lock=残留，现在证实 lock 文件与 handler 进程共存是正常状态
- **诊断修正**：lock 文件 + `ps aux | grep screen_trigger` 有输出 = handler 工作中；lock 文件 + 无进程 = 残留需清理

## 新增发现：冷却竞争

**产线观测**（00:50:39 → 00:50:55）：
```
[00:50:37] 处理完成 [silent]
[00:50:39] 冷却中(47s)，跳过
[00:50:55] 触发！开始分析屏幕...
[00:51:03] 场景类型: other
```

冷却（47s）与新触发间隔 16s，说明 watcher 在冷却期内仍检测到屏幕变化并触发。可能原因：
- handler 进程一直持有 lock，冷却期是 lock 释放前的阻塞
- 冷却逻辑在 handler 进程内，但 watcher 独立运行不受其控制

**建议**：watcher 端冷却与 handler 端冷却独立运行，需同步冷却计时器。

## 本次 session 新数据

**场景分布快照**（620 dry-run 条目，Jun 1 00:40 前）：
- `unknown`: 301 (49%)
- `browser`: 234 (38%)
- `desktop`: 42 (7%)
- `other`: 34 (5%)
- `wechat/calculator`: 9 (1%)

**否定词检测生产验证通过**：scene=other 的"没有需要处理的内容或异常"正确标记 [silent]。

**Gateway 污染**：1369 条（历史 1361 + 约 8 新增），~0.8 条/天，hook 实际已压制。
