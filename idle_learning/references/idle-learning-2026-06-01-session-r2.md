# 2026-06-01 空闲学习记录（方向D — 执行层/手眼配合精度）Session R2

**时间**：2026-06-01 00:22 +0800

**系统巡检**：
- Ollama: ✅ 运行中, models: qwen2.5:1.5b, qwen3-vl:2b
- screen_watcher: ✅ PID 97621 存活, 截图00:20 (3.3MB, 夜间正常)
- handler lock: ✅ 无残留
- auto_execute dry-run: ✅ 602条记录, 最近场景"other"
- 网络: ✅ github=200, hn=200, firebase=200（全部正常）

## 已实施改进（4项 handler 优化）

### 1. 夜间锁屏跳过检测（新增 is_dark_screenshot 函数）
- 问题：午夜到清晨 qwen3-vl:2b 每次锁屏截图仍执行 70-84s 完整分析
- 方案：10x10 缩略图体积判断 → 过暗截图直接跳过 scene classification + ask_screen
- 预期收益：夜间每次触发从 ~80s CPU 降至 ~0.5s（节省 ~98%）

### 2. 场景分类降速（max_w=800 → 400）
- 问题：get_scene_type() 800px resize 导致 qwen3-vl:2b 分析 35-47s
- 方案：分类分辨率降至 400px
- 预期收益：scene classification 35-47s → ~15-20s

### 3. unknown/other 场景紧急标记修复
- 问题：302 次 [urgent] 全部误标（qwen3-vl:2b 对空白屏幕幻觉出"异常"/"错误"）
- 方案：unknown/other 仅匹配 CRITICAL_KEYWORDS（错误/崩溃/异常/Error/crash），其余全部 silent
- 预期收益：减少 90%+ 虚假 [urgent] 推送

### 4. COOLDOWN_SECONDS 减半（120 → 60）
- 优化后 handler 更快 → 60s 冷却足够

**备份**：`screen_trigger_handler.py.bak.20260601_0022` → 有回滚能力

## 坐标校准研究（方向D核心发现）

### ⭐ POINTS-GUI-G-8B（arXiv 2602.06391, Feb 2026）
- **ScreenSpot-v2 95.7%** — 当前 SOTA（smolvlm2 的 61.71% → +34pp）
- **RL with Verifiable Rewards**：GUI grounding 天然适合 RL（奖励可验证、精度高）
- 三点成功：统一数据集 + 视觉编码器微调 + 强化学习
- 对 Hermes：auto_execute grounding 精度可通过 RL 持续提升

### ⭐ RULER tokens + I-MRoPE（arXiv 2510.03230, Oct 2025）
- 显式位置标记替代隐式坐标生成（类网格参考点）
- I-MRoPE 解决宽高维度不对称
- 最大改进在高分辨率界面 → 适用 Mac 大屏

### ⭐ DRS-GUI（CVPR 2026）
- Dynamic Region Search，免训练 GUI grounding
- ScreenSpot-Pro 提升 14%

### Qwen3-VL 坐标约定（GitHub #1560）
- [x, y] on **1000×1000 相对坐标 canvas**（非像素绝对坐标）
- 映射公式：x_px = x/1000 × W, y_px = y/1000 × H
- **对 DRY_RUN=False 最关键**：VLM 输出归一化坐标 → 像素映射

## 新发现

### The Website Specification（HN 346pts）
- https://specification.website/ — 平台无关网站规范
- **Agent Readiness 类别**（18 项标准）：llms.txt, MCP server, robots.txt, content negotiation
- 提供 MCP server + Agent Skill，可让 auto_execute 判断站点是否 agent-friendly

### 1-Bit Bonsai Image 4B（HN 47pts）
- 本地 4B 图像生成模型
- 潜在价值：若转本地视觉 grounding，可作 qwen3-vl:2b 的轻量补充

## 执行层全链路状态（实测 00:22）
```
screen_watcher (检测)       → ✅ PID 97621
screen_trigger_handler (分析) → ✅ 602 dry-run 记录
auto_execute() (dry-run)    → ✅ 602条
hermes_desktop_rpa.py (执行)  → ✅ click/press_key/paste_text 已实现
cliclick (手眼配合)          → ✅ /opt/homebrew/bin/cliclick
DRY_RUN                     → ⚠️ 仍为 True（安全模式）
```
全链路完整。下一步：坐标校准测试后切换 DRY_RUN=False。
坐标校准方案：qwen3-vl:2b 输出 1000×1000 相对坐标 → x_px = x/1000 × W 映射。
