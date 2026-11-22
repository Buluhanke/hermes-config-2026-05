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
  - 真人化操作
  - 自动化办公
---

# Hermes 真人化操作总路由

三大长期需求（办公软件 / 操作电脑 / 看懂网页）的统一决策入口。
**核心铁律（2026 五研究收敛）：code-first，截图是兜底不是默认。能读状态别读像素，能写代码别点坐标。**

## When to Use

任何「操作办公软件」「控制电脑/桌面」「读网页内容」的指令 → 先查此表选工具链，再动手。

## 三选一决策表

| 用户意图 | 第一优先（结构化/代码）| 第二（MCP/脚本）| 兜底（视觉）|
|---|---|---|---|
| **办公软件** Word/Excel/PPT | Python 直读写 `openpyxl`/`python-docx`/`python-pptx`（不启 WPS）| `mcp__wps_office__*` 33 工具（公式/图表/格式，需 WPS 开着，端口58891）| AX 树 → 截图|
| **操作电脑** GUI/桌面 | `mcp__agent_desktop__*` 67 工具（snapshot/click/type，AX 优先，不抢焦点）| `computer_use` / shell 脚本 | 截图→VLM（默认关）|
| **看懂网页** 任何 URL | XHR JSON / `web_extract` → markdown（L0/L2）| CDP `Runtime.evaluate` innerText、前端 AX 树 | Canvas/图片→OCR|

## 关键分工

- **办公**：纯数据处理（批量/不需渲染）用 Python 直读写；要公式计算/图表联动/在 WPS 里操作才用 MCP。Mac 版 WPS 无 VBA/COM，只能 MCP+Skills 或 Python。
- **电脑**：`cua-driver` 装在 `~/.local/bin/cua-driver`（不在 PATH，用全路径），后台 AX 操作不抢焦点。`agent_desktop` 67 工具是首选（无需调试端口）。
- **网页**：先拿数据不拿像素。读网页统一走 `browser-read-funnel` 的 6 脚本（`read_page.py`/`read_url.py`/`curl_xhr.py` 等）；登录态前台页用 `computer_use capture mode=ax` 读无障碍树。

## 感知漏斗（找元素/坐标时）

`perception-decision-engine` 4 层，已修复可用（2026-11-22）：
- L0 缓存 `perception_memory` ✅ `~/.hermes/perception_memory.db`（自建自学，命中 0.2ms）
- L1 AX 树 `cua-driver` ✅（全路径）
- L2 本地检测 `local_detector.py`（颜色/布局）+ `visual_verifier.py`（Vision OCR 带 bbox）✅ 已补齐
- L3 云 VLM `vlm_bridge.py` ✅ 默认禁用，需显式 set_enabled
- 验证：`python3 ~/.hermes/scripts/decision_engine.py stats`

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

## 避坑

- 技能文档状态会过期：用前实测（文件是否存在、命令是否在 PATH），不凭记忆。
- 网页读取不要先截图：截图是信息最差的一层（有损/慢/常失败）。
- Hybrid GUI 工具对非推理模型反而有害（-5.9pp），工具路由要显式不要隐式。
