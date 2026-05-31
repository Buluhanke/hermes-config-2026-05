# 2026-06-01 方向D学习记录 — 执行层/手眼配合

## 学习概况

**时间**：2026-06-01 02:01
**方向**：D — 执行层（手眼配合）
**来源**：idle_learning 第二循环（02:00 → 02:01 连续触发，第一个02:00覆盖方向C，本轮02:01覆盖方向D）

## 系统状态快照

| 指标 | 值 | 状态 |
|------|----|------|
| screen_watcher | PID 8748, 自01:27 | ✅ |
| 截图新鲜度 | 02:01, 3.3MB | ✅ |
| Ollama | qwen3-vl:2b + qwen2.5:1.5b | ✅ |
| 否定检测 | "没有需要处理的内容或异常" → [silent] | ✅ |
| 网络: github | ok | ✅ |
| 网络: HN | blocked | ❌ |
| web_search | 502 (SearXNG) | ❌ |
| ddgs | 正常 | ✅ |

## 产线快照（02:01，最近30条）

所有场景最近触发均为 "other" → 否定检测 → [silent]，无错误标记。

## 论文发现

### 1. GUI-Libra (arXiv 2602.22190v2)
- MSR/UIUC/UNC Chapel Hill, 57页, 2026-05-25 v2
- 开源native GUI agent 训练配方
- 核心问题：标准SFT + CoT推理会损害grounding
- Action-aware SFT：推理+直接动作混合训练
- KL信任区域稳定RLVR
- 发布81K数据集

### 2. LiteGUI (arXiv 2605.07505)
- 2026-05-08, 2B/3B轻量级
- 首次系统化蒸馏进GUI agent
- Multi-solution Dual-level GRPO

### 3. ClawGUI (arXiv 2604.11784)
- 2026-04-13, 浙江大学
- 首个开源全栈框架（训练+评估+部署）
- PRM步骤级监督

## Qwen3-VL 坐标公式

- 1000×1000 相对坐标 canvas
- 像素映射：x_px = round(x/1000 × W), y_px = round(y/1000 × H)
- 例：click(420,315) on 1920×1080 → (806, 340)

## 当前auto_execute瓶颈

9场景全部仅wininfo，动作利用率2.7%，缺少Verify阶段。

## 输出

日志已写入 `~/.hermes/memory/idle_learning_log.md`（从4266行追加至4369行）。
下次学习方向：B（ScreenParse + PaddleOCR-VL）
