---
name: hermes-mac-os-agent
description: Hermes Mac OS Agent 终极架构 — 7 层固定，4 原则，模型完全解耦。Apple 原生能力（AX+Vision+ScreenCaptureKit+CGEvent）做底，Skill 插件扩展。底层永远不变。
when_to_use: 设计/实现 Hermes 任何 Mac computer-use 功能、评估 Agent 架构、写新 Skill、对齐"真人化 Agent"目标时。
---

# hermes-mac-os-agent — 终极架构（已冻结）

## 七层固定结构

```
        Hermes Core
             │
   ┌─────────┴─────────┐
   ▼                   ▼
Task Scheduler    Skill Manager   ← 永不增加核心层
   │                   │
   └─────────┬─────────┘
             ▼
      Decision Engine            ← 模型完全解耦
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
AX Engine  Vision   OCR Engine     ← 3 个观察器
   │         │         │
   └─────────┼─────────┘
             ▼
       State Merger               ← Stateless
             ▼
      Action Executor             ← 4 种输出
             ▼
  ┌──────────┼──────────┐
  ▼          ▼          ▼
AX       CGEvent   AppleScript
             │
             ▼
      Verification Loop          ← 强制闭环
             │
             ▼
        SQLite Memory            ← 极简
```

## 四原则（不可违反）

### ① 模型完全解耦
- Hermes 不关心模型 (MiniMax / GPT / Claude / Qwen / DeepSeek / Gemini 全一样)
- LLM 只返回 action JSON:
  ```json
  {"action":"click", "target":"发送", "verify":{"app":"...","title_contains":"..."}}
  ```
- Runtime 负责执行

### ② 四种输入 + 四种输出（永不增加）

输入（观察器）:
- AX (真相)
- OCR (补丁)
- Vision (fallback)
- Events (执行后的世界变化)

输出（执行器）:
- Click
- Type
- Scroll
- Hotkey

### ③ Runtime 永远 Stateless
- **不做世界模型**
- **不存 UI tree**
- 每一步：重新观察 → 重新决策 → 重新验证
- Memory 只存：Task / History / Skill 状态

### ④ 所有动作必须闭环
```
Observe → Think → Act → Verify → Done
```
**永远不假设成功**。这是 90% Agent 失败的原因。

## Skill 插件化（唯一可扩展方向）

只增加 Skill，不动 Runtime：

- chrome.skill — 5 原子操作（find_url_bar/navigate/find_tab/click_login/fill_input）
- finder.skill — 文件操作
- xcode.skill — IDE 自动化
- cursor.skill — AI IDE 自动化
- photoshop.skill — 设计工具
- ...

每个 Skill 内部都是 Observe→Act→Verify 3 步模板。

## Mac Observer 统一接口

**只一个 Observer，不分 Chrome/Finder/Safari**：

```
mac_observe() → {
  ts, front_app, window, windows,
  elements, clickables, ocr,
  ocr_used, frame_diff
}
```

任何 App 都走这一条。`~/.hermes/scripts/mac_observe.py` 是 schema 唯一来源。

## Event Bus 优化（推荐加，但非必需）

- 订阅 `NSWorkspace.didActivateApplicationNotification`
- AXObserver + kAXValueChangedNotification
- 1Hz 兜底轮询（catch missed events）
- frame_diff > 0.05 才推 LLM，否则静默

## 资源预算（Mac mini M4 24GB）

| 模块 | 预算 |
|---|---|
| Hermes Runtime | 300-500 MB |
| AX Engine | <50 MB |
| OCR（按需） | <200 MB |
| Vision（按需） | <200 MB |
| SQLite | <20 MB |
| Skill Cache | <100 MB |
| **控制层总计** | **≤1GB** |

剩 23GB 给模型 + 其他应用。

## 决策流程（接任务时先跑这个）

### Step 0: 现状盘点（关键！避免"从零编译"反模式）
收到任何"用 Apple 原生能力做 X"的任务，**第一步不是开干**：
1. 列出已存在的现成能力（`mcp_cua_driver_*` / `vision_analyze` / `browser_vision` / `computer_use` 等）
2. 列出现状已验证的实测数字（延迟/精度/资源）
3. 比对"从零编译 Swift binary" vs "调用现成封装"的差距
4. **只有现成封装确实缺能力时才走原生编译**

### Step 1: 决策梯子（执行时按这个顺序）
```
1. AX 拿得到 → cua-driver get_window_state → click(element_index)  [30ms, 0 幻觉]
2. AX 拿到 role 但无 label (图标按钮) → zoom 区域截图 → vision_analyze  [500ms-4s]
3. AX 拿不到 (视频/Canvas/游戏) → take_screenshot → vision_analyze 全图  [3-4s]
4. 不确定操作结果 → 再 get_window_state 比对 frame_diff, >0.8 视为成功
```

### Step 1.5: 决策级联 (Decision Cascade) — 多级降级的协调铁律

观察器 AX/OCR/Vision 不是"选一个用",而是**有序级联**。命中即停,失败自动降级:

```
A. element_index → cua_click(element_index)         # AX 真相, 最稳, ~1ms
B. label 模糊匹配 elements[].title / ocr[].text      # ~50ms, 命中即 click(cx,cy)
C. bbox → click(cx, cy)                              # 有 frame 但无 label
D. vision_fallback_region(pid, win_id, x, y, w, h)   # 调 Gemini 兜底, 2-4s
```

铁律:
- **先便宜的**。A 不通才走 B,C 不通才走 D。vision_fallback 必须最后手段。
- **每级独立验证**。A 点击后跑 frame_diff,失败才降级,不能"我猜不行直接跳 D"。
- **D 必须有 cache**。同一区域同一问题 5 分钟内不重复调 Gemini (走 `vision_with_cache.cached_vision_analyze`,TTL=300s)。

完整实现见 `~/.hermes/scripts/mac_observe.py` 的 AGENT_PLAN 段,以及 `mac_vision_fallback.py` 的 `vision_fallback_region` 函数。

### Step 1.6: Vision 兜底层落地 (本次 session 沉淀)

3 块能力 (AX 真相 → OCR 补丁 → Vision 兜底), **含二级 provider 降级**:

| 能力 | 工具 | 实测 |
|---|---|---|
| AX 真相层 | `cua-driver get_window_state` + `mac_observe.py schema` + `hermes_native_eyes.py` 启发式按钮提取 | ✅ Chrome AX 30 元素带 frame |
| OCR 补丁层 | Vision.framework Swift binary + ScreenCaptureKit | ✅ 108 文字 900ms 稳态 |
| Vision 兜底层 (1 级) | `mac_vision_fallback.vision_fallback` → `vision_with_cache.cached_vision_analyze` → Gemini | ⚠ 走 agent 主链, CLI 模式不可用 |
| Vision 兜底层 (2 级) | `mac_vision_fallback._nv_vision_direct` → NVIDIA integrate Nemotron-VL 12B | ✅ 9.2s 真实跑通 |

**二级降级铁律** (新增, 解决"上游 provider 过期/欠费/超时"全场景):

```
vision_fallback(image, question)
  ↓ try 1 级: vision_with_cache (走 agent 主链, 自动有缓存)
  ↓   success? → return source=vision_with_cache
  ↓   fail (CLI 模式 / key 过期 / 模型 404) → 落 2 级
  ↓ try 2 级: _nv_vision_direct (NVIDIA integrate, 独立 API key)
  ↓   success? → return source=nv_vision_direct
  ↓   fail → return success=False, 报错含两级具体失败原因
```

**Provider 状态表** (2026-06-26 实测):

| Provider | 状态 | 端点 | 模型 | 备注 |
|---|---|---|---|---|
| Google Gemini | ❌ 过期 | generativelanguage.googleapis.com | gemini-3-flash-preview | API key 401/400 INVALID_ARGUMENT |
| 智谱 GLM-4V | ❌ 欠费 | open.bigmodel.cn | glm-4v-plus | HTTP 1113 "余额不足" |
| NVIDIA integrate | ✅ 可用 | integrate.api.nvidia.com | nvidia/nemotron-nano-12b-v2-vl | 70 字符 key 正常 |
| NVIDIA Qwen2-VL | ✅ 可用 | integrate.api.nvidia.com | nvidia/llama-3.2-90b-vision-instruct | 强需求换这个, Nemotron 弱 |

**Nemotron-VL 12B 弱点** (实测): 把 dock 图标当主 app 描述。**真用换 Qwen2-VL-72B 或 llama-3.2-90b-vision-instruct**——同 NVIDIA 端点, 改 `model` 参数即可。

集成脚本 (`~/.hermes/scripts/`):
- `mac_observe.py` — 统一 schema + 决策级联 plan
- `mac_vision_fallback.py` — Vision 兜底层 (`vision_fallback` 二级降级 + `vision_fallback_region` + `_cua_zoom_capture` + `_nv_vision_direct` + `e2e` CLI)
- `hermes_native_eyes.py` — 视觉中枢 schema + 启发式按钮提取
- `vision_with_cache.py` — 透明缓存层 (避免重复调 Gemini)

**SSL 坑** (新增, 2026-06-26): macOS 系统 Python 调 HTTPS API 必报 `CERTIFICATE_VERIFY_FAILED`。**修法**: 必加 `ssl.create_default_context(cafile=certifi.where())`, 不能用默认 `urlopen`。CI/容器环境若没 certifi, 装 `pip install certifi` 或 fallback `ssl.create_default_context()` (仍可能失败但至少不 ImportError)。

**集成验证套路** (解决"上游坏 vs 集成坏"区分, 已实战验证 2 次):

```python
# Monkey-patch 上游依赖, 验证下游函数契约
import vision_with_cache as vwc
def mock_cached_vision_analyze(image, prompt, **kw):
    return {"success": True, "analysis": "[MOCK] ...", "hit": False, ...}
vwc.cached_vision_analyze = mock_cached_vision_analyze

# 重 import 让 monkey-patch 生效
import importlib, mac_vision_fallback
importlib.reload(mac_vision_fallback)

# 真跑下游函数, 验证字段契约
r = mac_vision_fallback.vision_fallback("/tmp/test.png", "...")
assert r["success"] and "answer" in r and r["hit"] is False
# ✓ 上游失败 ≠ 集成 bug
```

**真 e2e 命令** (新增, 2026-06-26 实测 9.2s 跑通):
```bash
python3 ~/.hermes/scripts/mac_vision_fallback.py e2e
# 流程: screencapture 抓全屏 → vision_fallback 二级降级
# 期望: source=nv_vision_direct (因为 CLI 模式落 2 级), 9-10s 返 VLM 回答
```

完整对话细节见 `references/vision-fallback-integration.md`。

**补充参考文件**:
- `references/vision-fallback-integration.md` — Vision 兜底层真集成细节 + Mock 验证套路 + 验证命令清单
- `references/cua-driver-daemon-mcp-lifecycle.md` — cua-driver daemon + MCP launcher 双层生命周期（TCC 权限归属 + MCP 通道验证 + 恢复序列）
- `references/launchd-deployment.md` — macOS launchd 托管后台 daemon（plist 模板 + OOM self-protection 友好启动序列 + 手启动/launchd 并存清理 + 验证清单）

### Step 2: 失败处理
- 1 次失败 → 重新 observe + 尝试下级 fallback
- 2 次失败 → 切换相近 label 模糊匹配
- 3 次失败 → abort + 推送 Telegram 告警（写入 fact_store）

## 关键反模式（禁止）

❌ 维护世界模型（UI graph / world state）
❌ 存截图/OCR/UI tree 到磁盘
❌ 纯 VLM 喂截图（贵 + 慢 + 不稳）
❌ 多 Observer（Chrome Observer / Safari Observer 等等）
❌ 假设动作成功（不 verify）
❌ 给 Skill 加新核心层
❌ **"平台原生"= "从零编译" 错觉** — 优先用现成封装（如 cua-driver MCP 已经是 Apple 原生 AX/SDK/SCK 的封装 + 权限已开）
❌ **mss + pyautogui + 云端 VLM 反模式** — 慢 20-40x + 100% 幻觉 + 写死 key 不安全
❌ **写死 API_KEY** — 走 Hermes 已配置 model 字段（v2.8 不绑模型原则）

## 成功标准

跑起来后 Hermes 能：
- 自动登录任意网站
- 自动填表
- 自动切 tab
- 自动处理弹窗
- 自动搜索信息
- 自动恢复失败操作
- 切模型/换 Skill 不需要改 Runtime

## 何时升级

**不再升级核心层**。需要新能力 → 写新 Skill。

如果某天发现必须改核心才能做某事，先确认：
1. 是真的核心缺失，还是 Skill 写错？
2. 能用现有 3 个观察器 + 4 个执行器组合出来吗？
3. 不用改核心能不能绕过？

90% 情况下"必须改核心"是错觉。