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

## Qwen3-VL 坐标公式（2026-06-01 02:01 → 03:52 修正）

**⚠️ 以下为实测修正，覆盖上面错误记录**：
- Qwen3-VL 使用 **normalized 0-999 scale**（1000个整数点，0-based），不是 1000×1000！
- 正确映射公式（Qwen mobile_agent.ipynb 第50行，DeepWiki）：
  ```python
  def rescale_coordinates(point, width, height):
      point = [round(point[0]/999*width), round(point[1]/999*height)]
      return point
  ```
- 除数用 **999** 不是 1000（坐标范围 0-999 共 1000 个整数点）
- 例：click(420,315) on 1920×1080 → round(420/999×1920)=808, round(315/999×1080)=340
- 来源：https://deepwiki.com/QwenLM/Qwen3-VL/5.2-spatial-understanding-and-2d-grounding
- ⚠️ Ollama 版 qwen3-vl:2b 是否沿用此坐标约定待验证（DeepWiki 面向 Transformers 版）

## auto_execute 执行层盘点（2026-06-01 03:52 全面实测）

### RPA 执行层断链分析

auto_execute 的 4 段链路：
```
screen_watcher (检测变化) → screen_trigger_handler (分析) → auto_execute (dry-run) → RPA (执行)
                    ✅                           ✅                    ✅ 791条
```

### 可用动作池（三段执行层）

| 层 | 路径 | 动作数 | 关键函数 |
|----|------|--------|---------|
| RPA 脚本 | `~/.hermes/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py` | 11+ | ocr, click, press_key, paste_text, scroll, chrome_open_url, chatgpt_send, screenshot_region |
| 拟真动作 | `~/.hermes/hermes-humanization-core/humanization_core.py` | 10 | human_type, human_move, human_click, human_scroll, capture_screen, ask_vlm, vlm_click, find_element_by_vision |
| WHITELIST | screen_trigger_handler.py ACTION_WHITELIST | 3（none/wininfo/ocr） | 仅日志，不执行 |

**总可用动作池：21+ 种，WHITELIST 使用 3 种 → 利用率 ~14%**

### 4 个断链点
1. auto_execute → RPA 脚本桥接存在（`subprocess.run(['python3', RPA_SCRIPT, action, params])`），但 DRY_RUN=True 从不执行
2. 坐标映射链不存在（VLM 输出归一化坐标→屏幕像素坐标的转换函数未在 handler 中实现）
3. SafeGround 置信度框架未集成（不确定性量化/多采样/空间概率场）
4. 动作分级仅 3-tier（none/wininfo/ocr），未到 4-tier（Silent/Logged/Confirmed/Blocked）

### DRY_RUN=False 前置条件状态（03:52 验算）
| # | 条件 | 状态 | 备注 |
|---|------|------|------|
| ① 基线数据 | ✅ 791条 | 远超500条标准 |
| ② Ollama 稳定性 | ✅ 0% unknown | June 1 凌晨100% other |
| ③ 动作多样性 | ⚠️ 3种↑ | 从2→3（none/wininfo/ocr，本次改进后） |
| ④ 坐标映射链 | ❌ 未集成 | 公式已确认，函数未在 handler 中实现 |
| ⑤ SafeGround 置信度 | ❌ 未集成 | 不确定性量化/多采样缺位 |
| ⑥ 动作分级 | ⚠️ 部分 | binary→3-tier，未到 4-tier |

**6条件进度：①②✅ ③-⑥部分/未满足。安全过渡至少需要④⑤⑥全部到位。**

### 本次改进：ACTION_WHITELIST 动作多样性（已执行）
- 1688 场景从 `("wininfo", None)` → `("ocr", None)`（只读，安全）
- 验证：语法通过，DRY_RUN=True 下仅改变日志内容
- grep 验证：`grep "Would execute:" ~/.hermes/logs/screen_trigger.log | sort | uniq -c`

## 输出

日志已写入 `~/.hermes/memory/idle_learning_log.md`（从5614行追加至5684行）。
下次学习方向：A — 视觉层：qwen3-vl:2b vs gemma4:e4b 对比测试
