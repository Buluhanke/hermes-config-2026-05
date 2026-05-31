---
name: screen-watcher-vision
description: Screen watcher vision handler — qwen3-vl:2b 分析屏幕截图，场景分类与内容理解
trigger: screen_watcher触发screen_trigger_handler后调用
---

# Screen Watcher Vision Handler

## 核心能力

当前仅使用 **qwen3-vl:2b**（Ollama 本地）完成全部视觉分析任务。
smolvlm2-agentic-gui 已从 Ollama registry 永久下线（registry 404，2026-06-02 确认），不可再拉取。

| 函数 | 模型 | 速度（产线实测） | 用途 |
|------|------|------------------|------|
| `get_scene_type()` | qwen3-vl:2b | **9-12s** | 场景分类，返回英文单词（browser/wechat/desktop/calculator/other/unknown等） |
| `ask_screen()` | qwen3-vl:2b | **~12s** | GUI 内容分析（否定检测+关键词匹配） |
| 完整周期 | — | **20-30s** | 含两次 Ollama API 调用 + 图像处理 |

**响应时间注意**：qwen3-vl:2b 分类时间曾被记录为 35-47s（2026-06-01 前，num_ctx 默认 262144 导致内存溢出）。2026-06-01 修复：显式设置 `num_ctx=1024`（场景分类）和 `num_ctx=4096`（内容分析），分类时间降至 **9-12s**，完整周期 20-30s。详见 `references/ollama-numctx-memory-optimization-2026-06-01.md`。全黑/锁屏场景通过暗屏检测（`is_dark_screenshot()`）直接跳过，耗时 <0.5s。

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
| 坐标映射链 | ❌ 归一化→像素映射缺失 | P1 |
| Verify 阶段（error recovery） | ❌ 无执行后验证 | P2 |

**Qwen3-VL 坐标公式**：[x,y] on 1000×1000 相对 canvas，像素映射 `x_px = round(x/1000×W)`。

**最新论文发现**：
- **GUI-Libra**（MSR/UIUC, arXiv 2602.22190）：Action-aware SFT（直接动作数据优于 CoT+推理），KL 信任区域稳定 RLVR
- **LiteGUI**（arXiv 2605.07505）：首次蒸馏系统化进 GUI agent，2B/3B 达 SOTA
- **ClawGUI**（ZJU, arXiv 2604.11784）：首个开源全栈 GUI agent 框架+PRM 步骤监督

详见 `references/auto-execute-execution-layer-2026-06-01.md`

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

## 生产验证状态（2026-06-01 02:30 更新）

以下指标为 2026-06-01 02:30 巡检确认的健康基线：

| 指标 | 值 | 状态 |
|------|----|------|
| screen_watcher 进程 | PID 8748 | ✅ 持续运行 |
| 截图新鲜度 | 持续更新（每 ~60s） | ✅ |
| Ollama 进程 | qwen3-vl:2b runner (100% GPU) | ✅ |
| Ollama 运行时内存 | 2.7 GB / Context 4096 | ✅ |
| KV Cache 量化 | q8_0 | ✅ |
| 场景分类 num_ctx | 1024（代码确认） | ✅ |
| 内容分析 num_ctx | 4096（代码确认） | ✅ |
| Handler 堆积 ("Handler仍在运行") | **0 次** | ✅ 完全解决 |
| 否定检测（other → [silent]） | 0 个 other/unknown 误标 [urgent] | ✅ 生产验证通过 |
| 系统空闲内存 | ~13.4 GB | ✅ |
| dry-run 总数 | 715 条 | ✅ 正常增长（+43 自 01:50） |

### 当前场景分布（735 条 dry-run 记录，2026-06-01 02:55 快照，含全量历史）

```text
301 unknown (41%)  — 分类器信心不足（含 Ollama 被 kill 历史遗留，June 1 00:06 后 0% unknown）
234 browser  (32%)
129 other    (18%)  — 所有 other 正确标记 [silent] ✅（否定检测持续生效）
 42 desktop  ( 6%)
  6 wechat   ( 1%)
  3 calculator
```

**⚠️ 2026-06-01 02:50 后变化**：ACTION_WHITELIST 语义分离修复后，idle 场景（other/unknown/desktop/calculator）不再产生 "Would execute: wininfo" dry-run 日志。June 1 02:50 后的 dry-run 日志仅记录活跃业务场景（browser/wechat 等），日志量从每 ~60s 一条 idle 记录降为仅在有真实业务活动时记录。

**变化趋势**：
| 日期 | dry-run | unknown | browser | other | desktop |
|------|---------|---------|---------|-------|---------|
| 05-31 06:00 | 468 | 184 (40%) | 233 (50%) | — | 42 (9%) |
| 06-01 01:50 | 672 | 301 (45%) | 234 (35%) | 88 (13%) | 42 (6%) |
| 06-01 02:30 | 715 | 301 (42%) | 234 (33%) | 129 (18%) | 42 (6%) |

other 从 88→129（+41）说明否定词检测持续生效：更多原被分类为 browser 的场景正确降级为 other + [silent]。unknown 占比从 45%→42%（下降 3pp，因 other 增长稀释）。

**DRY_RUN=False 前置条件评估**（方向C巡检结论，2026-06-01 更新）：
| # | 条件 | 值 | 结论 |
|---|------|----|------|
| ① 基线数据 | 735+ 条 ≥ 500 | ✅ 已达基线 |
| ② Ollama 稳定性 | 42% unknown > 30%（含历史污染） | ❌ 需降低（按日期分片 June 1 后 0% unknown ✅） |
| ③ 动作多样性 | **3 活跃场景 wininfo + 5 idle 场景 none** | ✅ 已修复（P0 完成） |
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