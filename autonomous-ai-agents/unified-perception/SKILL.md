---
name: unified-perception
description: >-
  统一感知层（第7层）— PerceptionEngine 将 CDP AX树、桌面屏幕、Screenshot+OCR、Jina Reader
  合并为一个统一的感知接口。提供跨通道的 PerceptionElement 数据模型、ElementRegistry 跨turn追踪、
  以及LLM可读的 snapshot 格式。
version: 1.0.0
author: Hermes Agent
triggers:
  - 统一感知 / 感知层 / PerceptionEngine
  - 跨通道感知 / 混合感知 / 统一元素
  - "perception.py / perceive_what / perceive_element"
  - perception layer / unified perception
  - 元素注册表 / ElementRegistry / action tracking
  - CDP AX tree + OCR 融合 / 多源感知
  - 架构第7层 / 感知统一
tags: [perception, architecture, accessibility, ax, ocr, jina, element-registry]
---

> **⚠️ 关键陷阱（2026-05-28实测确认）**：
> `perception/` 目录**不存在**！SKILL.md 中描述的 `perception.py`、`perception/bridge.py`、`perception/world/state.py` 等都是**规划中的架构**，尚未实际构建。
> `HermesPerceptionBridge` 只是设计文档中的类名，不是可执行代码。
> 实际执行层仍依赖 `hermes_desktop_rpa.py` 的单文件脚本模式。
> 不要尝试 `from perception import ...` — 会失败。

# Unified Perception Layer — 统一感知层（架构第7层）

> **把 DOM 语义树 + OCR + 浏览器状态统一成一个感知接口，让 Agent 无论用浏览器还是桌面都能"看见"屏幕。**

## 架构总览

```
```perception.py (1424 lines)
│
├── PerceptionElement          — 跨所有通道共用的统一元素数据模型 (17个字段)
├── PerceptionSnapshot         — 一次感知的快照（元素列表 + 源信息 + 元数据）
├── ElementRegistry            — 跨会话/跨turn追踪元素操作历史
│
├── BrowserPerception          — CDP AX树后端（agent-browser CLI）
│   └── BrowserCDPPerceiver    — CDP supervisor 直连后端
├── ScreenOCRPerceiver         — 截图+百度OCR后端
├── DesktopAXUIPerceiver       — ✅ 新增：AppleScript AXUI桌面窗口结构后端
├── JinaURLPerceiver           — Jina Reader URL提取后端（内联）
│
├── PerceptionEngine           — 统一入口类
│   ├── perceive_browser()     → 浏览器CDP AX树
│   ├── perceive_screen()      → 桌面截图+OCR
│   ├── perceive_desktop()     → ✅ macOS桌面窗口AXUI结构
│   ├── perceive_url()         → Jina Reader网页提取
│   ├── perceive_auto()        → ✅ 自动嗅探可用源（CDP→AXUI→OCR）
│   └── format_snapshot_for_llm() → 格式化为LLM可读文本
│
└── 模块级助手函数
    ├── perceive_what("browser|screen|desktop|desktop:<app>|auto|url:...")
    ├── perceive_element("e1", "click")  # 记录操作
    ├── perceive_browser()
    ├── perceive_screen()
    ├── perceive_desktop("Google Chrome")  # ✅ 新增：桌面窗口感知
    └── perceive_auto({"type": "browser"})  # ✅ 新增：自动检测
```

## 核心数据模型

### PerceptionElement

```python
@dataclass
class PerceptionElement:
    perception_id: str          # 格式: "browser_cdp:page@e5" / "screenshot_ocr:region@ts"
    role: str                   # "button" / "textbox" / "heading" / "link" ...
    name: str                   # 显示文本（最多60字截断）
    value: str                  # 当前值（输入框内容等）
    description: str            # 辅助描述
    bounds: Optional[Tuple[int,int,int,int]]  # (x, y, w, h) 像素坐标
    clickable: bool
    editable: bool
    checked: Optional[bool]     # checkbox/radio 状态
    selected: bool
    url: str                    # 所属页面
    source: PerceptionSource    # 感知来源枚举
    confidence: float           # OCR置信度（CDP为1.0）
    raw: Dict                   # 原始数据（调试用）
    action_count: int           # 此元素被操作次数（跨turn累计）
    last_action: str            # 最后一次操作类型
    last_action_time: float     # 时间戳
```

### PerceptionSource (枚举)

- `BROWSER_CDP` — CDP Accessibility Tree（置信度1.0，有AX结构）
- `DESKTOP_AXUI` — macOS System Events（桌面窗口结构）
- `SCREENSHOT_OCR` — 截图+百度OCR（置信度0.7-0.9，无结构）
- `JINA_READER` — Jina Reader网页提取（无交互能力）
- `UNKNOWN` — 回退

### ElementRegistry

```python
reg = ElementRegistry()
ref = reg.register(elem)         # → "e1", "e2" ...（自动递增）
elem = reg.get_by_ref("e1")     # → PerceptionElement
elems = reg.all_elements()       # → list[PerceptionElement]
interactive = reg.interactive_elements()  # → 仅clickable/editable
reg.clear()                      # 页面变更时清空
reg.set_page_context(url)        # 标记当前页面URL
```

**关键行为：** `register()` 如果检测到 same `perception_id` 的已存在元素，会**合并状态**（保留 action_count、last_action 等历史），而不是覆盖。保证了跨turn的元素操作追踪。

## 感知源选择策略

| 场景 | 推荐 | 原因 |
|------|------|------|
| 浏览器已开启、有CDP | `perceive_browser()` | CDP AX树有结构和可信文本，操作可回溯到ref |
| 前端显示内容（图标/图片区域） | `perceive_screen()` | 无可读DOM文字时，OCR能读像素 |
| 后端/静态页面内容 | `perceive_url()` | Jina Reader直出markdown，不需开浏览器 |
| 混合验证 | 先 `perceive_browser()` 再 `perceive_screen()` | 用CDP做结构兜底，OCR做视觉确认 |

## Agent 调用方式

### 从 execute_code 调用（推荐）

```python
from perception import perceive_what, perceive_element

# 一次感知浏览器（同步包装器）
result = perceive_what("browser")
print(result)
# [Perception Source: browser_cdp]
# [URL: https://example.com]
# [Elements: 42 total, 18 interactive]
#
# Interactive elements:
#   @e1 [button] "登录"
#   @e2 [button] "注册"
#   @e3 [textbox] "搜索"
#   @e4 [link] "关于我们" (last: click x3)  ← 已经点过3次了

# Agent 操作后记录
perceive_element("e1", "click")
perceive_element("e3", "type")
```

### 感知屏幕

```python
result = perceive_what("screen")                      # 全屏
result = perceive_what("screen")  # or region=(0,0,800,600)  # 区域
```

### 感知URL

```python
result = perceive_what("url:https://news.ycombinator.com")
```

### 异步调用

```python
import asyncio
from perception import perceive_browser, perceive_screen, perceive_url

result = asyncio.run(perceive_url("https://example.com"))
```

## 集成点

### 当前状态
- `perception.py` 在 `~/.hermes/hermes-agent/perception.py`
- 所有助手函数可通过 `execute_code` 调用
- `get_engine()` 返回模块级单例（跨调用共享 ElementRegistry）
- `element_ref` 自动递增（e1, e2, ...），跨感知源统一编号

### 未来集成方向
1. **注册为Hermes工具** — 在 `run_agent.py` 中添加 `perceive` tool handler，让Agent直接调（不通过execute_code）
2. **CDP bounds解析** — 从 `getFullAXTree` 拿 `location` 字段补全 `bounds`
3. **跨会话持久化** — 将 ElementRegistry 接 Redis（元素操作历史跨对话保留）
4. ~~桌面 AXUI 集成~~ → ✅ **已完成** — `DesktopAXUIPerceiver` + `perceive_desktop()`
5. ~~自动回退~~ → ✅ **已完成** — `perceive_auto()` 自动嗅探 CDP → AXUI → OCR

## 与 hermes-rpa skill 的关系

| 层面 | hermes-rpa | unified-perception |
|------|-----------|-------------------|
| 抽象级别 | 战术层（怎么做） | 架构层（怎么感知） |
| 数据模型 | 无统一模型（各通道独立） | PerceptionElement 跨通道统一 |
| 操作追踪 | 无 | ElementRegistry 跨turn累计 |
| 格式输出 | 原始OCR文本 / CLI输出 | format_snapshot_for_llm() LLM优化 |
| 主要场景 | 执行点击/输入/滚动 | 感知输入+记录操作历史 |

**互补关系**：perception.py 提供"眼睛"，hermes-rpa 提供"手"。Agent 先用 perception 感知，再用 hermes-rpa 执行。

## 文件位置

- 主模块：`~/.hermes/hermes-agent/perception.py` (1424行)
- 不在 skills 目录下，作为 Hermes Agent 运行时模块使用
- 本 skill 仅作为文档和用法指南

## 两条感知架构路线（重要）

本 skill（unified-perception）和 `hermes-rpa` 中新增的 **Perception Kernel** 是两条平行架构：

| | unified-perception（本skill） | Perception Kernel（hermes-rpa/perception/） |
|---|---|---|
| 核心数据模型 | `PerceptionElement`（17字段，含action_count/last_action） | `UIObject`（10字段，含bbox/center/confidence） |
| 元素追踪 | `ElementRegistry`（ref自动递增，跨turn累计操作次数） | `WorldState`（世界状态管理器，含URL/hash/timestamp） |
| 融合策略 | `perception_id` 合并（same id → merge state） | IoU + text_similarity 规则融合 |
| 验证机制 | 无 | 5层 Verifier（URL→元素消失→hash→OCR→Vision） |
| 坐标系 | 无 | `CoordinateTransformer`（viewport↔screen↔Retina） |
| 鼠标抽象 | 无 | `MouseDriverFacade`（PyAutoGUI / CDP 双驱动） |
| 定位 | 感知输入 + 操作记录 | 感知 → 世界模型 → 可执行坐标 → 验证闭环 |
| 文件位置 | `~/.hermes/hermes-agent/perception.py` | `~/.hermes/hermes-agent/perception/` |

**关系**：`unified-perception` 提供跨通道统一感知接口，`Perception Kernel` 提供完整 GUI Agent Runtime。两者互补，Agent 用 `unified-perception` 感知，用 `Perception Kernel` 决策和执行。

**Perception Kernel 参考**：`hermes-rpa` skill → `references/perception-kernel-modules-2026-05-14.md`

**桌面Agent战略方向**：`hermes-rpa` skill → `references/desktop-agent-roadmap-2026-05-14.md`（路线图+现状+优先级）

## 参考文档

- `references/agent-browser-cli.md` — agent-browser CLI 用法
- `references/architecture.md` — 架构详解
- `references/desktop-agent-roadmap-2026-05-14.md` — **桌面全域Agent成长路线图**（战略方向+现状+下一步，源自hermes-rpa）

## 关键陷阱

1. **perception.py 不存在！** — ⚠️ 2026-05-28 实测确认：`~/.hermes/hermes-agent/perception.py` **不存在**，本 skill 描述的 `PerceptionEngine`、`PerceptionElement`、`ElementRegistry`、`HermesPerceptionBridge` 等都是**规划中的架构**，尚未实现为可执行代码。不要试图 import 或调用这些组件。
   - **实际可用感知**：由 `hermes-rpa` skill 的 `hermes_desktop_rpa.py` 统一入口提供（activate/click/type/send/readchat/ocr 等）
   - **实际视觉分析**：`screen-watcher-vision` skill 的 smolvlm2 截图分析
   - **perception/ 子目录**：不存在，`hermes-rpa` SKILL.md 中描述的 `perception/bridge.py` 等也是规划而非代码
   - **不要相信 SKILL.md 中的代码示例** — `from perception import perceive_what` 这类调用会失败

2. **模块级单例** — `get_engine()` 返回同一个 `PerceptionEngine` 实例，`ElementRegistry` 跨调用共享。如果要在独立环境中测试，手动 `PerceptionEngine()` 创建新实例。
2. **CDP后端依赖 agent-browser** — `BrowserPerception` 依赖 npx agent-browser CLI，如果 Hermes 浏览器网关未运行，会返回空元素列表。
3. **OCR后端需要网络** — `ScreenOCRPerceiver` 需要百度OCR API可达，且走 Clash 代理127.0.0.1:7897。
4. **Jina Reader也有代理依赖** — `perceive_url()` 默认走127.0.0.1:7897代理，如果代理未配置或网络不可达会报错。
5. **元素ref不跨页面持久** — 每次 `registry.clear()`（页面变更时）ref 编号重置。跨页面操作需要重新感知。
6. **CDP bounds通常为None** — CDP AX树不直接给像素坐标，需要额外 DOM 查询。但 `DesktopAXUIPerceiver` 的 AppleScript 后端自带像素坐标，`desktop` 源永远有 bounds。
7. **DesktopAXUIPerceiver 需要辅助功能权限** — 首次运行需在「系统设置 → 隐私与安全性 → 辅助功能」中允许 Terminal/Hermes。如果 `perceive_what("desktop")` 返回空结果，检查是否有该权限。
