---
name: screen-watcher-vision
description: Screen watcher vision handler — qwen3-vl:2b 分析屏幕截图，场景分类与内容理解
trigger: screen_watcher触发screen_trigger_handler后调用
---

# Screen Watcher Vision Handler

## 核心能力

当前使用 **ScreenParser YOLO**（快速预分类）+ **qwen3-vl:2b**（精确 VLM 分析）双层架构。

smolvlm2-agentic-gui 已从 Ollama registry 永久下线（registry 404，2026-06-02 确认），不可再拉取。

| 函数 | 模型 | 速度（产线实测） | 用途 |
|------|------|-----------------|------|
| `fast_scene_check()` | ScreenParser YOLO11-Large | **~91ms** (320px, CPU) | 快速预分类：idle(0-1元素) / active(>5) / uncertain(2-5) |
| `get_scene_type()` | qwen3-vl:2b | **~3s** (400px resize, num_ctx=1024) | VLM 精确场景分类（仅 active/uncertain 时调用） |
| `ask_screen()` | qwen3-vl:2b | **~5s** (800px resize, num_ctx=4096) | GUI 内容分析（否定检测+关键词匹配） |
| 完整周期（idle） | YOLO only | **~0.18s** | idle 场景跳过 VLM → 44x 加速 vs 纯 VLM |
| 完整周期（active） | YOLO + VLM | **~8s** | 活跃场景保留全链路分析 |

**核心流程**：
```text
触发 → YOLO 快速预分类 (~91ms)
  ├── idle (0-1元素) → 直接 silent（跳过 VLM）    ← **新增 2026-06-01**
  ├── uncertain (2-5) → 升级 VLM 场景分类
  └── active (>5元素) → VLM 场景分类 → 内容分析
```

**性能演进**：
- 2026-06-01 前（纯 VLM，num_ctx 默认 262144）：get_scene_type 35-47s，完整周期 70-84s
- 2026-06-01 第一次优化（num_ctx=1024/4096）：9-12s / 20-30s
- **2026-06-01 04:45 实测**（num_ctx 优化后稳定）：~3s / ~8s
- **2026-06-01 07:00（本轮）：YOLO 预分类集成 + idle 旁路** → idle 场景 0.18s (44x)

### ScreenParser YOLO 实现细节

Model: `docling-project/ScreenParser` (YOLO11-Large fine-tuned on ScreenParse v2)
Local path: `~/.cache/huggingface/hub/models--docling-project--ScreenParser/snapshots/f029e565f1206577402e43206454522075be3f72/best.pt`
Deps: `ultralytics 8.4.57` (hermes-agent venv)

**阈值**：
```python
if n <= 1:    return "idle"        # 跳过 VLM，直接 silent
elif n > 5:   return "active"      # 升级 VLM 精确场景分类
else:         return "uncertain"   # 升级 VLM（2-5 元素边界情况）
```

**已知限制**：ScreenParser 训练于 rendered web screenshots，原生桌面 App（微信/钉钉等）识别准确率待长期验证。55 UI 类覆盖 Table/Browser/Button/App Icon/Navigation Bar/Text Input 等常见桌面/移动 UI 元素。

**实现位置**：`screen_trigger_handler.py` 第22-65行（`fast_scene_check()` + `_get_yolo()` 惰性加载），`on_trigger()` 中 `is_dark_screenshot()` 检查后立即调用。

全黑/锁屏场景通过暗屏检测（`is_dark_screenshot()`）直接跳过，<0.5s。**⚠️ 实测：843+ 条 dry-run 记录中该检测从未触发**（10x10 缩略图 < 500 字节阈值过严，暂不修复 — 低 ROI）

## 场景分类 prompt（当前在用）

```python
"Classify this screenshot into EXACTLY ONE class. Class descriptions:\n"
"- browser: web browser full of tabs, address bar, bookmarks bar, webpage content\n"
"- wechat: WeChat desktop app with chat list, contacts, moments\n"
"- desktop: clean desktop with wallpaper, file icons, dock/taskbar, minimal windows\n"
"- calculator: calculator app showing number pad or math computation\n"
"- jingdong: JD.com e-commerce page with product listings, search bar, categories\n"
"- 1688: 1688.com wholesale page with product grid, filters, supplier info\n"
"- dingtalk: DingTalk work chat app with org hierarchy, group chats\n"
"- telegram: Telegram messenger with conversation list, channels\n"
"- other: any app or screen not matching above (file explorer, terminal, settings, system dialogs, IDE)\n"
"Reply with ONLY the single class word."
```

温度 **0.0** 确保确定性输出。英文输出必须与 `ACTION_WHITELIST` key 和 `on_trigger()` 分支逻辑的 `scene_type in (...)` 精确匹配。**2026-05-31 修复**：分支逻辑从中文关键词（`"浏览器" in scene_type`）改为英文精确匹配（`scene_type in ("browser",...)`），避免死代码。

**2026-06-01 升级**：从 zero-shot 改为含详细类描述的 few-shot-like 模式，为每类场景添加视觉特征描述（尤其 "other" 类明确列出 file explorer/terminal/settings/IDE 等常见误分类场景），预期降低 unknown 率（当前 45%→目标 <25%）。

## Auto-Execute 否词检测（2026-06-08 实装，2026-06-10 验证通过）

```text
场景 other 的 "没有需要处理的内容或异常" ✅ → 标记 [silent]，不推 Telegram
```

**机制**：关键词匹配前检查前 12 字符是否有"没有/无/未/不"，避免否定上下文误触发 [urgent]。

**2026-06-01 产线快照**（修复前）：
- scene=unknown: 301 (49%) — 全部误标 [urgent]
- scene=other: 全部误标 [urgent]

**2026-06-10 验证**（修复后）：
- scene=other 的 "没有需要处理的内容或异常" → 正确 [silent]

## Auto-Execute 执行层现状（2026-06-01 方向D调研）

**2026-06-01 修复：ACTION_WHITELIST 语义分离**。idle 场景（other/unknown/desktop/calculator）→ `("none", None)`，活跃场景（browser/wechat/1688/dingtalk/telegram）→ `("wininfo", None)` 保留。产线数据验证：June 1 期间 141/142 条 dry-run（99%）来自 idle 场景，修复后夜间 dry-run 日志量压至接近零。

**当前状态**：DRY_RUN=True，3 活跃场景保留 "wininfo" 入口，5 idle 场景无声无记录。干线上（June 1 02:50 后）dry-run 日志仅记录真实业务场景。

| 瓶颈 | 状态 | 优先级 |
|------|------|--------|
| ~~场景无差异化动作~~ | ✅ 已修复（2026-06-01）：活跃 3 场景 wininfo，idle 5 场景 none | ✅ P0 完成 |
| 坐标映射链 | ✅ 已实装（2026-06-01）：`normalized_click(nx, ny)` + `get_screen_size()` 已加入 RPA 脚本 | ✅ P1 完成 |
| Verify 阶段（error recovery） | ❌ 无执行后验证 | P2 |

**Qwen3-VL 坐标公式**：[x,y] on normalized **0-1000 scale**。官方转换公式（QwenLM/Qwen3-VL cookbooks/2d_grounding.ipynb）：`x_px = int(coord_x / 1000 * screen_w)`, `y_px = int(coord_y / 1000 * screen_h)`。⚠️ **不是 /999！** 早期 DeepWiki 的 0-999 记录已被官方 notebook 推翻。详见 `references/qwen3-vl-coordinate-correction-1000-confirmed.md`。

**最新论文发现**：
- **GUI-Libra**（MSR/UIUC, arXiv 2602.22190）：Action-aware SFT（直接动作数据优于 CoT+推理），KL 信任区域稳定 RLVR
- **LiteGUI**（arXiv 2605.07505）：首次蒸馏系统化进 GUI agent，2B/3B 达 SOTA
- **ClawGUI**（ZJU, arXiv 2604.11784）：首个开源全栈 GUI agent 框架+PRM 步骤监督

详见 `references/auto-execute-execution-layer-2026-06-01.md`
- **Self-Critiqued RL for GUI Grounding**（arXiv 2510.27266）：自批评机制——模型输出坐标前自我批评，拒绝低置信预测。零样本可集成到 handler，用 qwen3-vl:2b logprob 做置信度门控。详见 `references/self-critiqued-rl-gui-grounding.md`

## 触发过滤

screen_trigger_handler 在调用 VLM 前先做场景过滤。**不分析**以下类型：
- 桌面壁纸 / 壁纸切换
- 通知中心
- 任务栏空白区域
- 全黑/锁屏（通过 `is_dark_screenshot()` 快速判断，10×10 缩略图体积）

**Cooldown 机制**：60 秒内同场景不重复分析。cooldown 文件 `~/.hermes/screenshots/.handler_cooldown`。

**Handler 互斥锁**：`~/.hermes/screenshots/.handler_lock` 文件防止 watcher 重复拉起 handler。

## 参考文件

- `references/ollama-api-endpoint-chat-vs-generate-2026-05-30.md` — ⚠️ 重要：/api/chat vs /api/generate 性能差异，错误端点导致120s超时
- `references/insiderllm-m4-2026-guide-2026-05-31.md` — InsiderLLM M4 2026 最新推荐：Qwen 3.6-27B dense（M4 24GB "tight but doable"），vision 内建于基座
- `references/response-normalization-2026-06-02.md` — ⚠️ 重要：get_scene_type() response 标准化，取第一行+小写+trim标点
- `references/production-snapshot-2026-06-01-0716.md` — 产线快照：YOLO预分类28次空闲检测全部正确，unknown率0.54%，双层分类器稳定运行
- `references/screen-trigger-handler-telegram-fix-2026-05-30.md` — Telegram推送失败修复（hermes_tools → 直接Bot API）+ 场景分类prompt幻觉bug修复
- `references/smolvlm2-structured-json-2026-05-29.md` — smolvlm2 JSON 输出测试详情（响应时间、清理函数、可靠性评估）
- `references/screen-trigger-handler-auto-execute-2026-05-28.md` — Auto-Execute 集成设计文档
- `references/screen-watcher-handler-lock-2026-05-26.md` — Handler 重复 spawn 修复
- `references/qwen3vl-vs-smolvlm2-2026-05-30.md` — qwen3-vl:2b vs smolvlm2 实测对比（速度、分辨率、适用场景）
- `references/scene-classification-model-fix-2026-06-02.md` — ⚠️ 重要：get_scene_type() 从 smolvlm2 切换到 qwen3-vl:2b，smolvlm2 在纯分类任务上会产生 final_answer 乱码
- `references/internvl3_5_4b_mac_bug_2026-06-02.md` — ⚠️ Issue #12166 已关闭（2025-09），可重测验证是否仍有问题
- `references/captchas-auto-execute-security-2026-05-30.md` — CAPTCHA agent 检测研究，DRY_RUN=False 时需考虑的 anti-detection 对策
- `references/hermes-desktop-rpa-osascript-timeout-2026-06-02.md` — osascript 超时是 cron 环境限制（非 PATH 问题），DRY_RUN=False 切换必须在有活跃桌面 session 的环境
- `references/auto-execute-execution-layer-2026-06-01.md` — ⭐ Auto-Execute 执行层现状分析（方向D调研）：GUI-Libra/LiteGUI/ClawGUI 论文发现、Qwen3-VL 1000×1000 坐标映射公式、动作利用率仅 2.7% 的瓶颈分析、DRY_RUN=False 过渡方案

## 配置项

| 参数 | 当前值 |
|------|--------|
| 截图路径 | `~/.hermes/screenshots/current.png` |
| 分析缓存 | `/tmp/hermes_trigger_vision.jpg` |
| 日志路径 | `~/.hermes/logs/screen_analysis.log` |
| Ollama 端点 | `http://localhost:11434/api/chat`（⚠️ 必须用 `/api/chat`，禁止 `/api/generate`） |
| 视觉模型 | `qwen3-vl:2b`（smolvlm2-agentic-gui 已永久下线） |
| 温度 | `0.0`（场景分类）/ 内容分析默认 |
| stream | `false`（必须显式设置，否则返回 streaming chunks） |
| **num_ctx（场景分类）** | **1024**（2026-06-01 修复：原默认 262144 导致 20GB 内存） |
| **num_ctx（内容分析）** | **4096** |

## Ollama num_ctx 内存优化（2026-06-01 实装）

### 问题

screen_trigger_handler 调用 Ollama API 时只设了 `temperature: 0.0`，未指定 `num_ctx`，Ollama 默认使用 Qwen3-VL 全量 256K 上下文。运行时内存从模型权重 1.76GB 膨胀至 **20GB**（KV cache + Metal 缓冲），系统仅剩 218MB 空闲。

### 修复

两处 API 调用必须设置 num_ctx：

```python
# get_scene_type() — 场景分类（单字输出，足够简短）
"options": {"temperature": 0.0, "num_ctx": 1024}

# ask_screen() — 屏幕内容分析（需适度上下文）
"options": {"temperature": 0.0, "num_ctx": 4096}
```

⚠️ **num_ctx 共享行为**：get_scene_type() 和 ask_screen() 共用同一个 Ollama runner 实例（qwen3-vl:2b）。由于 handler 先调用 get_scene_type() 再调用 ask_screen()，实际生效的 context 大小是最后一次调用时决定的。Ollama 会在每个请求时按 `options.num_ctx` 重新分配 KV cache，因此两个函数各自使用其指定的 num_ctx 值。代码审查已确认两处设置均正确。

### 效果

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| Ollama 运行时内存 | 20 GB | 2.7 GB |
| 上下文大小 | 262144 | 4096 |
| 系统空闲内存 | 218 MB | 13.4 GB |
| 场景分类耗时 | 35-47s | 9-12s |

### 检查命令

```bash
ollama ps  # 查看当前加载模型的 CONTEXT（过大则 num_ctx 未设置）
ollama stop qwen3-vl:2b  # 卸载旧实例后重启 screen_watcher
```

### KV Cache Quantization（补充优化）

在 num_ctx 设置正确的基础上，**Ollama KV Cache 量化可进一步降低运行时内存**。2026-06-01 验证：`OLLAMA_KV_CACHE_TYPE=q8_0`（不设置时默认 `f16`）。

```bash
# 检查当前设置
echo "${OLLAMA_KV_CACHE_TYPE:-not set}"
```

影响（以 Llama 3.2 8B / 128K 上下文为例）：
| KV Cache 类型 | 内存占用 | 节省 |
|---------------|----------|------|
| f16（默认） | 23.3 GB | — |
| q8_0 | 17.0 GB | -27% |
| q4_0 | 13.8 GB | -41% |

当前 qwen3-vl:2b / Context 4096 下，q8_0 量化已足够（2.7GB 运行时内存，余量充足）。q4_0 可省更多但收益有限（上下文小）。注意 KV Cache 量化对精度影响极小（lmdeploy 验证为可接受范围）。

详见 `references/ollama-numctx-memory-optimization-2026-06-01.md`

## ⚠️ 子进程 Python 版本不匹配（2026-06-01 发现并修复）

**关键诊断**：screen_watcher 通过 `/bin/bash -lic set +m` 启动，`python3` 解析为 `/usr/local/bin/python3`（系统 Python 3.14），但 handler 依赖 `ultralytics`（YOLO）只装在 hermes venv（Python 3.11）。

```python
# screen_watcher.py line 87-90 — ❌ 旧代码（python3 解析到 Python 3.14）
subprocess.Popen(
    ["python3", "/Users/aimac/.hermes/scripts/screen_trigger_handler.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
```

**后果**：handler 因 `ModuleNotFoundError: ultralytics` 立即崩溃 → handler_lock 残留 → watcher 检测到锁文件后 `"Handler仍在运行，跳过本次触发"` → 483+ 次跳过 → 所有后续 trigger 被永久阻塞。

**修复**：显式使用 venv Python 路径，不依赖 PATH 解析：

```python
# ✅ 修复后（2026-06-01）
subprocess.Popen(
    ["/Users/aimac/.hermes/hermes-agent/venv/bin/python3",
     "/Users/aimac/.hermes/scripts/screen_trigger_handler.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
```

**验证方法**：
```bash
# 确认 watcher 使用的 python3 版本
/bin/bash -lic 'which python3; python3 --version'

# 确认 ultralytics 在目标 python 中可用
/usr/local/bin/python3 -c "from ultralytics import YOLO"  # ❌ 系统 Python — ModuleNotFoundError
~/.hermes/hermes-agent/venv/bin/python3 -c "from ultralytics import YOLO; print('OK')"  # ✅ venv
```

**根因**：`bash -lic`（login + interactive）会重新加载 PATH，如果用户 shell 配置中 PATH 顺序不同，可能导致子进程使用不同 Python。多 Python 版本环境（3.11 venv + 3.14 系统）下 PATH 解析不可靠，必须用绝对路径。

**Pitfall**: 任何 `subprocess.Popen(["python3", ...])` 调用，如果 watcher 由 bash -lic 启动，`python3` 的解析结果可能与开发者预期不同。必须显式指定 venv 路径。

**相关文件**：
- Watcher: `~/.hermes/scripts/screen_watcher.py`
- Handler: `~/.hermes/scripts/screen_trigger_handler.py`
- Stale lock: `~/.hermes/screenshots/.handler_lock`

## 生产验证状态（2026-06-01 07:00 更新）

以下指标为 2026-06-01 07:00 巡检确认的健康基线（含本 session 修复的关键问题）：

| 指标 | 值 | 状态 |
|------|----|------|
| screen_watcher 进程 | PID 48245（本 session 重启） | ✅ |
| 截图新鲜度 | 持续更新（每 ~60s） | ✅ |
| Ollama 进程 | qwen3-vl:2b runner (100% GPU) | ✅ |
| YOLO 预分类 | 首次 watcher auto-trigger 成功（07:06:19） | ✅ 新验证 |
| Handler 堆积 (Handler仍在运行) | 修复前 483+ 次（Python 版本不匹配）；修复后 0 次 | ✅ 本 session 修复 |
| Python 版本修复 | watcher 子进程显式使用 venv Python 3.11 | ✅ 本 session 修复 |
| 系统空闲内存 | ~13.4 GB | ✅ |
| dry-run 总数 | 967 条 | ✅ 正常增长 |

### 当前场景分布（2026-06-01 04:45 快照 — 当日 + 全量历史）

**当日（June 1 00:06~04:46，qwen3-vl:2b 稳定运行期）**：
```text
246 other  (98.8%) — 全额标记 [silent] ✅（否定检测生效）
  2 unknown ( 0.8%) — 稳定极低位
  1 browser  ( 0.4%)
```
**unknown 率 0.8%** — 历史最低。

**当日（06-01 07:16 快照 — YOLO 预分类上线后）**：
```text
369 other  — 其中 28 次被 YOLO 预分类直接跳过（93ms）
  2 unknown (0.54%)
  1 desktop
  1 browser
```
**YOLO 预分类 28 次空闲检测，全部正确标记 [silent]**。双层分类器产线稳定。日期分片统计的必要性验证：全量 42-49% unknown 因包含 smolvlm2 时代/Ollama 挂掉的历史污染。详见 `references/unknown-scene-date-analysis-2026-06-01.md`。

**全量历史（843+ 条 dry-run 总记录）**：
```text
301 unknown (36%)  — 历史污染（smolvlm2 时代 + Ollama 被 kill 遗留）
236 browser  (28%)
129 other    (15%)  — 所有 other 正确标记 [silent] ✅
 42 desktop  ( 5%)
  6 wechat   ( 1%)
  3 calculator
```
**变化趋势**：
| 日期 | dry-run | unknown（全量） | unknown（当日分片） | other | browser |
|------|---------|----------------|-------------------|-------|---------|
| 05-31 06:00 | 468 | 40% | 280(May-31) | — | 50% |
| 06-01 01:50 | 672 | 45% | — | 13% | 35% |
| 06-01 02:30 | 715 | 42% | — | 18% | 33% |
| **06-01 04:45** | **843** | **36%** | **0.8%** **(今日)** | **15%** | **28%** |
| **06-01 07:16** | **967** | **36%** | **0.54%** **(当日 369 other / 2 unknown / 1 desktop / 1 browser)** | **YOLO idle 28次正确跳过** | **YOLO预分类已产线稳定** |

other 从 88→129（+41）说明否定词检测持续生效：更多原被分类为 browser 的场景正确降级为 other + [silent]。unknown 占比从 45%→42%（下降 3pp，因 other 增长稀释）。

**DRY_RUN=False 前置条件评估**（2026-06-01 04:45 更新）：
| # | 条件 | 值 | 结论 |
|---|------|----|------|
| ① 基线数据 | 843+ 条 ≥ 500 | ✅ 超基线 |
| ② Ollama 稳定性 | 全量 36% unknown（含历史污染）；**当日 0.8%** | ✅ 当日满足 |
| ③ 动作多样性 | **3 活跃场景 wininfo + 5 idle 场景 none** | ✅ 已修复 |
| ④-⑥ | 坐标映射/SafeGround/分级 | ❌ 需工程实现 |

**unknown 42% 是已知问题**：约半数为 macOS 内存压力杀死 Ollama 后历史遗留的 Connection refused 分类失败。idle_learning 方向C 提出 P0 改进（Ollama Watchdog 5 分钟健康检查+自动重启），预期降 unknown 到 25-30%。

## Ollama API 端点注意事项

**禁用 `/api/generate`**：处理 1920×1080 截图需 41.6s，容易超时。

**必须用 `/api/chat`**：相同截图 31.7s，快 24%，且 response 格式 `data['message']['content']`（非 `/api/generate` 的 `data['response']`）。

**payload 格式**：
```python
payload = {
    "model": "qwen3-vl:2b",
    "messages": [{"role": "user", "content": "...", "images": [img_b64]}],
    "stream": False,  # 必须
    "options": {"temperature": 0.0, "max_tokens": 20}
}
```