# DRY_RUN=False 切换准备条件 — R3 评估（2026-06-01 03:08）

## 产线快照

| 指标 | 值 | 状态 |
|------|-----|------|
| screen_watcher | PID 8748, 01:27 启动 | ✅ |
| 截图新鲜度 | 03:04, 3.2MB | ✅ |
| Ollama 进程 | 存活, qwen3-vl:2b 已加载 | ✅ |
| Ollama 内存 | 2.7GB (100% GPU), context=4096 | ✅ |
| 模型列表 | qwen2.5:1.5b + qwen3-vl:2b | ✅ |
| DRY_RUN 总量 | 747 条 | ✅ |
| June 1 unknown | 0% (00:07 后) | ✅ |
| 动作分布 | none=12, wininfo=736 | ❌ 仅2种 |
| Handler lock | 无残留 | ✅ |
| Telegram | 未配置 (BOT_TOKEN/CHAT_ID 缺失) | ⚠️ |
| gateway.log 污染 | hook 已禁用，不增长 | ✅ |

## 6 条件诊断（R3, 2026-06-01）

### 条件① 基线数据 — ✅ 747 ≥ 500
最新命令：`grep -c "AUTO-EXEC-DRY" ~/.hermes/logs/screen_trigger.log` → 747

### 条件② Ollama 稳定性 — ✅ 0% unknown
- `ps aux | grep ollama` → 进程存活
- `curl -s http://127.0.0.1:11434/api/tags` → qwen2.5:1.5b + qwen3-vl:2b
- `grep "2026-06-01" ~/.hermes/logs/screen_trigger.log | grep "场景类型:" | sort | uniq -c | sort -rn` → 0% unknown (00:07 后)
- Ollama 运行时: `ollama ps` → qwen3-vl:2b, 2.7GB, 100% GPU, context=4096

### 条件③ 动作多样性 — ❌ 仅2种
诊断：`grep "Would execute:" ~/.hermes/logs/screen_trigger.log | sort | uniq -c`
```
12 Would execute: none for...
736 Would execute: wininfo for...
```
**RPA 脚本支持 11 种动作**：wininfo, ocr, click, type, press, openurl, send, readchat, scroll, activate, url
**ACTION_WHITELIST 仅使用 2 种**：none（idle），wininfo（全部业务场景）

**瓶颈**：所有业务场景（browser/wechat/1688/dingtalk/telegram）全部映射到 `("wininfo", None)`。
Scene 类型多 ≠ 动作多样性。

**P0 修复方案**：
```python
ACTION_WHITELIST = {
    "browser": ("wininfo", None),    # 获取窗口信息
    "wechat": ("activate", "WeChat"),  # 激活微信窗口
    "1688": ("ocr", "screen"),       # OCR扫描屏幕
    "dingtalk": ("activate", "DingTalk"),
    "telegram": ("wininfo", None),
    # idle场景
    "desktop": ("none", None),
    "other": ("none", None),
    "unknown": ("none", None),
    "calculator": ("none", None),
}
```
可立即达到 ≥3 种动作，满足条件③。

### 条件④ 坐标映射链 — ❌ 未实现
- `grep -r "normalized_click\|1000/1000" ~/.hermes/scripts/` → 空
- `ask_screen()` 返回纯文本，无归一化坐标输出
- Qwen3-VL 1000×1000 归一化约定（来自 GitHub #1560）未实现
- `click` 动作未在 ACTION_WHITELIST 中出现

**Qwen3-VL 坐标公式**：
- VLM 输出 [x, y] on **1000×1000 相对坐标 canvas**
- 像素映射：x_px = x/1000 × W, y_px = y/1000 × H

### 条件⑤ 置信度/不确定性量化 — ❌ 缺位
- `grep -r "confidence\|multi_sampl\|uncertainty\|SafeGround\|logprob" ~/.hermes/scripts/screen_trigger_handler.py` → 空
- 仅有否定词检测（检查关键词前12字符是否有"没有/无/未/不"）
- 无 logprob 几何平均、无多采样、无概率分布

**候选方案**：
1. **AutoFocus** (arXiv 2605.02630) — training-free token-level perplexity 不确定性
2. **AVR** (arXiv 2603.12823) — logprob 几何平均，θ_high=0.85, θ_low=0.60
3. **SafeGround** (UCSB AI, Feb 2026) — 空间不确定性量化

### 条件⑥ 动作分级 — ❌ 缺位
- 当前仅二分：idle→none, business→wininfo
- 无 Silent/Logged/Confirmed/Blocked 四级权限模型
- 无场景间 privilege 差异

**参考模型（生产级共识）**：
- **Silent**：只读操作（截图分析、场景分类、信息检索）
- **Logged**：文件写入（日志、文件修改）
- **Confirmed**：Shell/网络/跨应用（需 Telegram 确认）
- **Blocked**：凭据/系统修改

## Handler 代码结构摘要

| 位置 | 功能 | 参数 |
|------|------|------|
| Line 21 | Ollama API endpoint | `http://localhost:11434/api/chat` |
| Line 22 | MODEL | `qwen3-vl:2b` |
| Line 23 | SCREENSHOT_SMALL | `/tmp/hermes_trigger_vision.jpg` |
| Line 27 | COOLDOWN_SECONDS | 60 |
| Line 30-32 | RPA_SCRIPT path | `~/.hermes/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py` |
| Line 33 | DRY_RUN | `True` |
| Line 35-46 | ACTION_WHITELIST | 9 scenes → only 2 unique actions |
| Line 97 | resize_for_vision default | max_w=800 for ask_screen |
| Line 124-125 | ask_screen resize | 800px |
| Line 144 | num_ctx | 4096 for ask_screen |
| Line 148 | ask_screen timeout | 120s |
| Line 159 | get_scene_type resize | max_w=400 |
| Line 173 | num_ctx | 1024 for scene classification |
| Line 177 | get_scene_type timeout | 60s |

## 判断逻辑

1. 条件①②③任一不满足 → 记录可执行改进，不推进
2. 条件①②③满足 + ④⑤⑥部分满足 → 推进坐标映射（P0）
3. 全满足 → 设计梯度过渡方案

## P0-P3 改进计划

| 优先级 | 改进项 | 前置条件 | 预期效果 |
|--------|--------|---------|---------|
| P0 | 扩展 ACTION_WHITELIST 差异化动作 | 仅需编辑 handler | 满足条件③ |
| P1 | 验证 qwen3-vl:2b 量化校准 | 检查当前 quantization | 提升 scene classification 稳定性 |
| P2 | 坐标映射 prototype | 条件③满足后 | 为 DRY_RUN=False 打下基础 |
| P3 | AutoFocus 概念验证 | 条件④有进展后 | 添加置信度量化 |
