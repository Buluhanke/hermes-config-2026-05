---
name: hermes-runtime-fortress
description: 守护 Hermes 自身在 Mac mini 24GB 上的运行时 — 浏览器识别 4 层方法论 (CDP DOM / AX 树 / 浏览器内 VLM / OCR 兜底)、内存自保护 (watchdog + cron + Hermes-pid 黑名单)、空间记忆缓存。涉及 Hermes 自我保护 / 浏览器自动化决策 / 屏幕识别的本地替代路径 / 内存告警 / 进程优先级 时必加载。
when_to_use: 浏览器自动化选型 / CDP vs AX 决策 / 屏幕识别的本地替代路径 / 内存超 75% 告警 / 写 watchdog 类脚本 / 设计 Hermes 自愈系统时。
---

# hermes-runtime-fortress — Hermes 自身运行时堡垒

**核心原则**: Hermes 是这台 Mac mini 的数字主人（见 SOUL.md 主宰宣言）。两个互补方向：

1. **浏览器识别 4 层方法论**: CDP DOM-id 稳定层 → AX 树结构层 → 浏览器内 VLM 视觉层 → OCR 兜底层。**弃屏幕截屏+本地 VLM 路线**（耗 17GB RAM、精度低、用户决定卸载 Ollama 2026-07-04）。
2. **内存自保护**: watchdog 监控 + 三级响应 + Hermes-pid 黑名单，绝不自杀。

---

## 一、浏览器识别 4 层方法论

### 方向调整背景（Ollama 阶段教训）

2026-06-28 装 Ollama + llava:7b → 3 大致命问题：
1. **精度低**: LLaVA 7B 自拼 JSON prompt 在 canvas/表格/颜色编码/按钮意图分类幻觉率高，UI grounding ~60%（vs UI-TARS 94%）
2. **吃 17GB RAM**: Ollama 进程独占 67.3% 统一内存，挤掉 Hermes 自保护缓冲
3. **冷启动 13s**: 首跑要加载 4.7GB 模型，UX 差

**结论（2026-07-04 用户指令）**: Ollama 已彻底删除。本地 VLM 路线 ROI 不及浏览器原生能力，改用浏览器原生识别栈。

### 4 层降级决策表

| 优先级 | 层级 | 工具 | 适用场景 | 速度 | 准确率 |
|---|---|---|---|---|---|
| L0 缓存 | spatial_memory 命中 | `~/.hermes/spatial_memory/` | 同窗口第二次操作 | < 100ms | 100% |
| L1 DOM-id | `page.domCua.getVisibleDom()` | CDP DOM 节点 ID（dev-browser） | 表单/按钮/链接精确点击 | 200ms | 100% |
| L2 AX 树 | `mcp_cua_driver_get_window_state` | macOS Accessibility 树 | Safari/Chrome 结构化字段 | 500ms | 95% |
| L3 浏览器内 VLM | Playwright `page.snapshotForAI()` + 云端 LLM | 页面原生无障碍快照 | 复杂 SPA/canvas/iframe | 1-3s | 90% |
| L4 OCR 兜底 | `mcp_cua_driver_get_window_state` + regex | 屏幕文字匹配 | 全部失败的最后手段 | 1-2s | 70% |

**为什么不本地 VLM**: 本地 VLM 吃 17GB RAM，云端 VLM 延迟 1-3s 但精度高 + 0 RAM 占用，**云端成本 < 本地 RAM 成本**。

### 浏览器识别 5 步自检 SOP

**每次新会话 / 长时静默后 / 用户首次提问前**，必跑：

```bash
# 1. Chrome CDP 9222 在跑?
lsof -i :9222 2>/dev/null | grep -q LISTEN && echo "CDP OK"

# 2. cua-driver 健康?
mcp_cua_driver_health_report

# 3. 当前活跃 Chrome 窗口?
mcp_cua_driver_list_windows --on_screen_only

# 4. dev-browser domCua 是否装好?
ls ~/.hermes/node_modules/@sawyerhood/dev-browser 2>/dev/null && echo "domCua OK"

# 5. 有未完成任务?
ls ~/.hermes/tasks/*.md 2>/dev/null | xargs grep -L "状态: DONE" 2>/dev/null | head -3
```

**缺哪个补哪个，不问用户**（章程硬规则）。

### L1 DOM-id 稳定层（首选）

**dev-browser** 项目的 `page.domCua.*`（6.3k stars，2026-07 更新）：
```js
const snapshot = await page.domCua.getVisibleDom();  // {entries: [{ref, line}], truncated, docToken}
await page.domCua.click({ nodeId: refFor("Submit 按钮"), waitForNavigation: false });
```
**vs Hermes CDP**: dev-browser 提供 **稳定 ref ID**（sticky public_id），Hermes CDP 每次返回新 selector。

### L2 AX 树结构层（次选）

```bash
mcp_cua_driver_get_window_state --pid <chrome_pid> --window_id <wid>
```

**AX tree 0 nodes 触发器**: `elements: []` 但 `tree_markdown` 有内容 → 窗口在后台/最小化 → `bring_to_front` 后重抓。

### L3 浏览器内 VLM 视觉层（兜底，用云端不用本地）

```js
const result = await page.snapshotForAI();  // {full: 'accessibility tree markdown'}
// → 喂给云端 LLM（OpenRouter / Gemini / Anthropic）
```

### L4 OCR 兜底层（最差，慎用）

`mcp_cua_driver_get_window_state` 拿不到 AX 时 → regex 屏幕文字匹配。

---

## 二、内存自保护

### 三级响应 (内存超 75% 时)

| 等级 | 触发 | 动作 | 影响 |
|---|---|---|---|
| L1 警告 | 内存 ≥ 75% | 清理 chrome-devtools-mcp / 缓存进程 | 无感 |
| L2 紧急 | 内存 ≥ 85% | 停非核心 cron / 暂停 background 任务 | 影响 cron |
| L3 自杀保护 | 内存 ≥ 95% | Hermes 核心进程永不杀；可砍非核心 Python 子进程 | 极端 |

### Hermes-pid 黑名单（核心进程保活）

```bash
CORE_PIDS=$(pgrep -f 'hermes_cli.main|hermes-gateway|cua-driver')
# 内存紧张时杀 chrome-devtools-mcp / 非核心进程，绝不杀 CORE_PIDS
```

**注意（2026-07-04）**: 已删除本地 Ollama/LLaVA，之前依赖卸载 LLaVA 释放内存的逻辑已失效。

### watchdog 模式 (cron `*/5`)

```bash
*/5 * * * * /bin/bash ~/.hermes/scripts/memory_watchdog_cron.sh >> ~/.hermes/memory_watchdog.log 2>&1
```

**自洽性铁律**: 心跳频率 vs idle 阈值必须 `heartbeat_interval < idle_threshold / 2`。
- 修复前: heartbeat=5min, idle_threshold=10min → 临界
- 修复后: heartbeat=5min, idle_threshold=20min → 安全 5 < 10

**分两轨时间戳**: `last_beat` (活着) ≠ `last_action_at` (在干活)。`check_idle()` 永远用 `last_action_at`。

---

## 三、空间记忆缓存 (L0 层)

**`~/.hermes/spatial_memory/`**: 同一窗口第二次出现直接命中缓存，0 tool call。

```python
# key = (pid, window_id, semantic_hash)
# value = {elements: [...], last_seen: ts, ttl: 300}
```

**适用**: 用户连续在同一个 Chrome 窗口做操作、桌面 app 周期性弹窗。
**不适用**: 窗口内容动态变化快（视频播放、实时聊天）、用户首次访问某个 app。

---

## 四、launchd plist 排查（2026-07-04 落地）

**触发条件**: 用户报"X 一直刷屏" / "定时通知没完" / "取消 cron 无效" → **第一时间查 launchd**。`cronjob list` 只覆盖 Hermes 内部 cron，macOS `launchd` 是独立调度系统。

### 3 处必查（并行）

```bash
# 1. Hermes 内部 cron
hermes cron list

# 2. macOS launchd plist
launchctl list | grep -i hermes

# 3. crontab
crontab -l 2>/dev/null
```

### launchd 环境 gh/keychain 失效模式（2026-07-04 实录）

```
gh auth status  → 显示 "✓ Logged in" (读 hosts.yml 元数据)
gh auth token   → "no oauth token found" (查 keychain → token 失效)
gh api user     → 401 Requires authentication
```

**教训**: 状态命令 ≠ 真实验证，必须实际调 `gh api user` 才有意义。
**修法**: `GH_TOKEN` 环境变量注入 plist，或用户重新 `gh auth login`。

### plist 字段常见坑

| 字段 | 错误 | 正确 |
|---|---|---|
| `StartInterval` | 1800 (30 分钟) | 86400 (1 天) |
| `RunAtLoad` | 删了 | `<true/>` |
| `EnvironmentVariables.GH_TOKEN` | 直接 Set 不存在字段 | 先 Add 再 Set |
| `StandardOutPath` | `~/log/...` | `/Users/<u>/.hermes/logs/...` |

**铁律**: plist 写完 `plutil -p` 读回验证，不信注释。

---

## 五、备份系统监控 SOP（2026-07-04 新增）

### 3 类备份 + 验证命令

| 备份类型 | 仓库 | 远程验证 |
|---|---|---|
| 加密整盘 `.gpg` | `hermes-backup` | `gh api repos/Buluhanke/hermes-backup/git/matching-refs/heads/backup-` |
| git 可视 skills | `hermes-backup-v2` | `gh api repos/Buluhanke/hermes-backup-v2/commits --jq '.[0].commit.author.date'` |
| 整库加密推送 | `hermes-backup` 分卷 | `git -C ~/.hermes/.backups/staging/github branch -r` |

### 监控 SOP（每周至少一次）

```bash
# 加密整盘层
GH_TOKEN="$GITHUB_MCP_TOKEN" gh api repos/Buluhanke/hermes-backup/git/matching-refs/heads/backup- \
  --jq '.[].ref' 2>/dev/null | sort -r | head -1

# git 可视层（容易忽略！必须并行查）
GH_TOKEN="$GITHUB_MCP_TOKEN" gh api repos/Buluhanke/hermes-backup-v2/commits \
  --jq '.[0].commit.author.date' 2>/dev/null
# > 30 天前 → hermes-git-backup.sh 没挂 cron，需重挂
```

### git 可视备份重建步骤

```bash
# 1. 确认脚本存在
ls ~/.hermes/scripts/hermes-git-backup.sh

# 2. 检查是否在 crontab 里
crontab -l 2>/dev/null | grep hermes-git-backup

# 3. 如果没有，挂 Hermes cron（每周日凌晨 3:05）
hermes cron create \
  --name "git-skills-backup" \
  --schedule "5 3 * * 0" \
  --prompt "bash ~/.hermes/scripts/hermes-git-backup.sh >> ~/.hermes/.backups/git-backup.log 2>&1" \
  --deliver origin

# 4. 立即手动触发
bash ~/.hermes/scripts/hermes-git-backup.sh 2>&1
```

---

## 六、Ollama/Docker 清除记录（2026-07-04 用户指令）

### 已执行清理

| 清理项 | 动作 |
|---|---|
| `config.yaml` auxiliary.vision | `provider: auto`，删除所有 ollama 硬编码 |
| `memory_watchdog.py` | 删除 `ollama_stop()` / `ollama_running_models()` 函数；DANGER 动作改为杀 chrome-devtools-mcp |
| `memory_watchdog_cron.sh` | 删除 `ollama stop llava:7b` 调用 |
| `idle_driver.py` | Ollama 检查 → 改为 CPU 核心数检查 |
| `fact_semantic_search.py` | `ollama nomic-embed-text` → OpenAI `text-embedding-3-small` API |
| `self_heal_watchdog.sh` | 删除 Ollama 11434 检查整块 |
| `MEMORY.md` / `SOUL.md` | 所有 ollama/llava 引用改为"云端VLM" |

### 已删除文件

```
hermes_web_local.py        (整体基于 Ollama)
vlm_bridge.py / run_vlm_loop.sh
mac_vision_fallback.py
vision_cache.py / _browser.py / _with_cache.py
visual_verifier.py / local_detector.py / screen_turing_test.py
screen_watcher.py / screen_trigger_handler.py
```

### 未动文件（不在调度中，deprecated-2026-07-04/ 目录留档）

`hermes_browser_use.py`、`hermes_web_auto.py`、`speak_route.py`、`vlm_playwright_loop.py` 等 — 均无 cron/launchd 调度，已归档备查。

### vision 当前架构

```
auxiliary.vision: provider=auto（已改）
  → 1. OpenRouter（主模型有 vision） ✅
  → 2. Nous Portal ✅
  → 3. Native Anthropic ✅
fact_semantic_search: OpenAI text-embedding-3-small API（已改）
```

---

## 关联

- `hermes-see-act` — L1/L2/L3/L4 决策调用此 skill
- `references/launchd-plist-gotchas.md` — plist 字段陷阱完整版
- `references/gh-keychain-launchd-gotcha.md` — gh token 失效完整修复链
- `references/browser-4-layer-decision.md` — 4 层降级决策表 + 基准数据
