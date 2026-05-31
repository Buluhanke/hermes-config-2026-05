# Auto-Execute 执行层现状分析（Direction D 调研）
**日期**：2026-06-01 02:01
**来源**：idle_learning 方向D — 执行/手眼配合

## 当前 auto_execute 状态快照

```
ACTION_WHITELIST (9 场景):
  browser/wechat/1688/dingtalk/telegram/desktop/calculator/other/unknown
  全部 → (wininfo, None)

RPA_SCRIPT: hermes_desktop_rpa.py 支持 8 个动作:
  wininfo, click, type, press, openurl, send, readchat, scroll
  仅 wininfo 被 auto_execute 使用（2.7% 的动作利用率）

DRY_RUN=True
所有 682 条 dry-run 记录全部是 "Would execute: wininfo"
```

## 关键瓶颈

| 瓶颈 | 状态 | 优先级 |
|------|------|--------|
| 所有场景无差异化动作 | ❌ 9 场景全 wininfo | P0 |
| 坐标映射链 | ❌ VLM 输出归一化坐标→无像素映射 | P1 |
| Verify 阶段（error recovery） | ❌ 无执行后验证 | P2 |
| 动作分级（Silent/Logged/Confirmed） | ❌ 仅有 DRY_RUN 开关 | P2 |

## Qwen3-VL 坐标约定（DRY_RUN=False 切换核心公式）

**坐标系**：1000×1000 相对坐标 canvas（GitHub #1560 确认）
**像素映射公式**：
```
x_px = round(x / 1000 × W)
y_px = round(y / 1000 × H)
```
**示例**：qwen3-vl 输出 click(420, 315) on 1920×1080
- x = 420/1000 × 1920 = 806.4 → 806
- y = 315/1000 × 1080 = 340.2 → 340

**实现方式**：hermes_desktop_rpa.py 中新增 `normalized_click(nx, ny, screen_w, screen_h)` 函数

## 新增论文发现

### GUI-Libra（arXiv 2602.22190v2，2026-05-25，MSR/UIUC/UNC）
- **核心问题**：标准 SFT + CoT 推理会损害 grounding 精度
- **Action-aware SFT**：混合推理→动作 + 直接动作训练数据，对动作和 grounding token 重加权
- **KL 信任区域**：RLVR 训练中 KL 正则化对离线→在线预测可预测性至关重要
- **Success-adaptive scaling**：降权不可靠的负梯度
- **发布**：81K GUI reasoning 数据集 + 代码 + 模型
- **对 auto_execute 启发**：直接动作数据比 CoT 推理对 grounding 更友好；KL 正则化启示场景分类 temperature=0 但动作预测需保留熵

### LiteGUI（arXiv 2605.07505，2026-05-08）
- **Guided On-policy Distillation**：首次将知识蒸馏系统化引入 GUI agent
- **Multi-solution Dual-level GRPO**：宏观子任务规划 + 微观执行匹配
- 2B/3B 级别超越传统模仿学习上限
- **对 auto_execute 启发**：可蒸馏 qwen3-vl:2b 到更小模型（如 Vocaela-500M）提升速度

### ClawGUI（arXiv 2604.11784，2026-04-13，ZJU）
- 第一个开源全栈 GUI agent 框架（训练+评估+部署三合一）
- **Process Reward Model (PRM)**：步骤级密集监督
- ClawGUI-2B：17.1% MobileWorld GUI-Only
- **对 auto_execute 启发**：PRM 可直接用于 Verify 阶段（每步动作后验证结果）；混合 CLI-GUI 控制架构

## 可执行改进

1. **🔴 action_whitelist 场景特异性扩展（P0）**：
   ```python
   ACTION_WHITELIST = {
       "browser": ("wininfo", None) + ("scroll", -3)  # 差异化动作
       "desktop": ("wininfo", None)  # 只读
       ...
   }
   ```

2. **🟡 normalized_click 函数（P1）**：
   ```python
   def normalized_click(nx, ny, screen_w=1920, screen_h=1080):
       x = round(nx / 1000 * screen_w)
       y = round(ny / 1000 * screen_h)
       return click(x, y)
   ```

3. **🟢 Verify 阶段（P2）**：参考 ClawGUI PRM + GUI-Agent-Harness 4-phase loop
4. **🟢 GUI-Libra 81K 数据集**：github.com 已恢复，可下载用于未来 grounding 训练
