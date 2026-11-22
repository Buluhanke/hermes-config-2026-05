---
name: hermes-humanlike-ops
description: 真人化办公电脑网页总路由 code-first选工具链。Use when 用办公软件/操作电脑/看懂网页
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [office, computer-use, browser, perception, router]
    related_skills: [perception-decision-engine, browser-read-funnel, wps-office-mac-automation, computer-use-agents-2026]
triggers:
  - 用办公软件
  - 操作电脑
  - 看懂网页
  - 操作手机
  - 刷课时
  - 答题
  - 真人化操作
  - 自动化办公
---

# Hermes 真人化操作总路由

四大长期需求（办公软件 / 操作电脑 / 看懂网页 / 操作手机）的统一决策入口。
**核心铁律（2026 五研究收敛）：code-first，截图是兜底不是默认。能读状态别读像素，能写代码别点坐标。**

## When to Use

任何「操作办公软件」「控制电脑/桌面」「读网页内容」「操作手机 App」的指令 → 先查此表选工具链，再动手。

## 四选一决策表

| 用户意图 | 第一优先（结构化/代码）| 第二（MCP/脚本）| 兜底（视觉）|
|---|---|---|---|
| **办公软件** Word/Excel/PPT | Python 直读写 `openpyxl`/`python-docx`/`python-pptx`（不启 WPS）| `mcp__wps_office__*` 33 工具（公式/图表/格式，需 WPS 开着，端口58891）| AX 树 → 截图|
| **操作电脑** GUI/桌面 | `mcp__agent_desktop__*` 67 工具（snapshot/click/type，AX 优先，不抢焦点）| `computer_use` / shell 脚本 | 截图→VLM（默认关）|
| **看懂网页** 任何 URL | XHR JSON / `web_extract` → markdown（L0/L2）| CDP `Runtime.evaluate` innerText、前端 AX 树 | Canvas/图片→OCR|
| **手机 App** | `uiautomator dump` 控件树（text/resource-id/bounds，零识别误差、毫秒级）| adb `input tap/text/keyevent` 按 bounds 执行 | 截图 → 百度 OCR（仅纯图片页/Canvas）|

## 关键分工

- **办公**：纯数据处理（批量/不需渲染）用 Python 直读写；要公式计算/图表联动/在 WPS 里操作才用 MCP。Mac 版 WPS 无 VBA/COM，只能 MCP+Skills 或 Python。
- **电脑**：用 Hermes pinned 的驱动 `~/.hermes/tools/cua-driver-0.21.0-darwin-arm64/CuaDriver.app/Contents/MacOS/cua-driver`（版本要与插件 SDK 匹配），后台 AX 操作不抢焦点。`agent_desktop` 67 工具是首选（无需调试端口）。
- **网页**：先拿数据不拿像素。读网页统一走 `browser-read-funnel` 的 6 脚本（`read_page.py`/`read_url.py`/`curl_xhr.py` 等）；登录态前台页用 `computer_use capture mode=ax` 读无障碍树。
- **手机**：流程与坑点全部沉在 `android-control`（含无线连接、熄屏/锁屏下操作、输入框陷阱、root 设备装 App）。关键：adb 命令用全路径 `/Users/aimac/.local/bin/adb`；感知用 `uiautomator dump` 而不是截图 OCR；屏幕熄/锁不影响 adb，但刷脸类认证必须本人做。

## 感知漏斗（找元素/坐标时）

`perception-decision-engine` 4 层，已修复可用（2026-11-22）：
- L0 缓存 `perception_memory` ✅ `~/.hermes/perception_memory.db`（自建自学，命中 0.2ms）
- L1 AX 树 `cua-driver` ✅（全路径）
- L2 本地检测 `local_detector.py`（颜色/布局）+ `visual_verifier.py`（Vision OCR 带 bbox）✅ 已补齐
- L3 云 VLM `vlm_bridge.py` ✅ 默认禁用，需显式 set_enabled
- 验证：`python3 ~/.hermes/scripts/decision_engine.py stats`

### per-step 动作验证闭环（2026-11-22 新增，UIAnchor/V-Droid 核心）

找元素只解决「点哪」，不保证「点到了、生效了」。`step_verifier.py` 补上动作后的结果感知：
- `precheck(target_spec, screenshot)` — 动作前校验目标还在、还是那个东西（走 4 层漏斗）。
- `postcheck(expected_spec, before, after)` — 动作后强制重抓，验证期望状态：`text_appears` / `text_gone`（OCR）+ `fp_changed`（整图指纹）。OCR 读不到不误判（标记 inconclusive），由 fp 兜底。
- `run_step(step_id, intent, target_spec, expected_spec, action_fn, screenshot_before, screenshot_after_fn)` — 完整闭环：前校验失败则**中止不执行动作**；动作后验证失败自动重试一次，仍失败 → escalate_to_human。
- trace 落盘 `~/.hermes/step_trace.jsonl`（buffer 批量写，防 fd 泄漏），可审计每一步。
- 自检：`python3 ~/.hermes/scripts/step_verifier.py selftest`（6/6，纯本地不依赖 OCR/屏幕）。
- 铁律：**任何状态改变的操作（提交/支付/删除/转发开关）都必须过 run_step**，不能只 find_element 后直接点——这是「模型对了但点错了」的解药。

## 真人化三支柱

1. **不抢焦点**：CDP 隐藏 Chrome、镜像登录态 profile、窗口最小化；禁止前台抢鼠标键盘。
2. **分层感知**：95% 走 L0/L1，VLM 只兜底 0.1%；token/延迟省 10-100×。
3. **终身学习**：L1 成功写 L0，miss 后人工操作一次即记住 → 下次 0ms 命中。

## 自检（多轮实测，2026-11-22）

测试脚本：`~/.hermes/cache/scratch/smoke_humanlike.py`（临时目录会被清理，必要时重建）

三遍运行结果：**11/11 通过（100%）**
- 感知：L0 缓存写入→读回命中 3 轮（x=10/20/30）、指纹稳定性、颜色块检测、引擎 stats 均 ✅
- 办公：python-docx 写入→读回 3 轮 ✅（注：openpyxl/pptx 系统 python 未装，Excel/PPT 走 WPS MCP 或其他 venv）
- 网页：read_url.py 真实读 example.com 3 轮全走 curl 层（577 chars）✅

环境事实：系统 python 有 `docx`/`PIL`，无 `openpyxl`/`pptx`；`cua-driver` 在 `~/.local/bin/cua-driver`（不在 PATH）；`decision_engine.py` 修复后可正常运行。

## 操作电脑链路实测（2026-11-22，真点击）

崩溃根因 + 修复：`computer_use` 报 `session setup failed (TaskGroup)` → `hermes computer-use doctor` 显示 `incompatible daemon: contract version 0.8.0 does not match SDK 0.7.0`。根因是 `~/.local/bin/cua-driver`(v0.26, contract 0.8) 占着 socket，而 Hermes pinned 的是 `~/.hermes/tools/cua-driver-0.21.0-darwin-arm64/`(v0.21, SDK 0.7)。
- 修复：`~/.local/bin/cua-driver stop` 停掉 v0.26 serve → 用 pinned 0.21 二进制 `serve --no-overlay` 后台启动 → doctor 全绿（session active / AX trusted / TCC granted）。
- ⚠️ 别用 ~/.local/bin 的 0.26 启动 serve，必和插件 SDK 版本冲突；版本必须匹配 pinned。

真实操作闭环（全 background 不抢焦点）：
1. `computer_use list_windows` → 拿到目标 pid/window_id
2. `capture(mode='ax', pid, window_id)` → 106+ 元素全拿到
3. 文本框：`set_value(element, value, delivery_mode='background')` → `effect: confirmed` + value_readback（文本框不要点，AXPress 返回 -25206）
4. 文本区：`click(coordinate, background)` 投递 → `type(text, background)` → `effect: confirmed`
5. 再 `capture` 读回 → 元素 label 变成输入内容 = 验证成功
- 坐标是 native 空间（元素 bounds 直接可用），不是截图像素。
- osascript 开窗口会卡 TCC 弹窗，改用已存在窗口或 computer_use 自身。

## 避坑

- 技能文档状态会过期：用前实测（文件是否存在、命令是否在 PATH），不凭记忆。
- 网页读取不要先截图：截图是信息最差的一层（有损/慢/常失败）。
- Hybrid GUI 工具对非推理模型反而有害（-5.9pp），工具路由要显式不要隐式。
