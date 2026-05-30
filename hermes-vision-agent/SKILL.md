---
name: hermes-vision-agent
description: "Phase 2 核心：视觉全域感知，看见桌面、控制一切软件。"
---

# hermes-vision-agent

**Phase 2 核心**：视觉全域感知，看见桌面、控制一切软件。

## 核心能力

```
See(截屏) -> Think(VLM分析) -> Act(拟真点击)
```

## 依赖

- `hermes-humanization-core`（必须先安装）
- Ollama 本地视觉模型（见下方当前可用模型）
- pyautogui + mss（系统控制）

### 当前本地模型状态（2026-06-01，aimac清理后）

| 模型 | 大小 | 状态 | 用途 |
|------|------|------|------|
| qwen2.5:1.5b | 986 MB | ✅ 可用 | 轻量文本推理 |
| qwen3-vl:2b | 1.9 GB | ✅ 可用 | **主VLM**（轻量级视觉理解） |
| qwen3-vl:latest | 6.1 GB | ❌ 已删 | 6GB太大，M4 24GB吃不消 |
| smolvlm2-agentic-gui | 2.0 GB | ❌ 已删 | 占用资源 |

> **内存原则（aimac）**：24GB Mac mini跑不动6GB模型+qwen3-vl:2b双VLM。优先保留轻量模型，释放内存优先于模型性能。
> qwen3-vl:2b (1.9GB) 是当前唯一VLM，响应较快。

## 典型用法

```python
from vision_agent import vlm_click, ask_screen, find_element_by_vision

# 1. 直接找按钮并点击（最常用）
vlm_click("加入进货单")

# 2. 问当前屏幕一个问题
answer = ask_screen("这个1688商家评分是多少？")
print(answer)

# 3. 先找坐标，确认后再点
coords = find_element_by_vision("确认付款按钮")
if coords:
    human_click(*coords)
```

## 1688 场景

```python
from vision_agent import search_1688, add_1688_to_cart

search_1688("纸箱 50*40*30")
add_1688_to_cart()
```

## 微信场景

```python
from vision_agent import wechat_send_image

# 发送图片给老板
wechat_send_image("/tmp/报价单.png", contact_name="老板")
```

## 桌面应用

```python
from vision_agent import find_and_open_app

# 打开 Safari
find_and_open_app("Safari")
```

## ⚠️ Chrome GPU合成层截屏限制（2026-06-01实测）

**问题**：`CGWindowListCreateImage`截不到Chrome内容——Chrome渲染到GPU合成层，不画到屏幕缓冲区。

**现象**：
- `screencapture -x` 或 `Quartz.CGWindowListCreateImage` 对Chrome窗口返回空白/RGBA(0,0,0,0)
- `computer_use` capture也会失败（底层同用CGWindowListCreateImage）
- Vision OCR对Chrome永远返回空

**实测验证**：
- 激活Chrome窗口后screencapture → PNG存在但内容为空白或浏览器UI
- 即使前台窗口正确，CGWindowListCreateImage也截不到Chrome网页内容

**影响范围**：
| 方案 | 对Chrome可用？ | 替代方案 |
|------|---------------|----------|
| screencapture + Vision OCR | ❌ 失效 | 无需替代 |
| computer_use capture | ❌ 失效 | 使用browser工具 |
| browser_snapshot (DOM) | ✅ 完美 | 主感知方案 |
| mcp_chrome截图 | ❌ MCP不可用 | 用browser_snapshot |

**结论**：Chrome GPU合成层是macOS安全限制，无法绕过。**正确做法是不截Chrome屏，用DOM/AX Tree读内容**。

**正常工作的组合**：
```
browser_snapshot(DOM 8ms) → LLM分析 → browser_click/type执行
```
这本身就是完整闭环，无需截图OCR兜底。

---

## 已知局限
- qwen3-vl:2b 响应约 **2-4秒**（1.9GB轻量模型，M4 24GB流畅）
- 找元素需要描述尽量具体："发送按钮" 比 "按钮" 效果好
- 文件对话框目前需要手动介入（VLM无法操作 macOS 原生文件选择器）
- Chrome GPU合成层 → 截屏方案全部失效，用browser_snapshot替代
- smolvlm2 和 qwen3-vl:latest 均已删除（内存优化）；VLM能力减弱但OCR仍正常


## 闭环验证（2026-05-31）

**浏览器表单提交任务：感知→执行→验证 完整跑通**

- `browser_snapshot` AX Tree: 8ms, 19元素, ref索引精准
- `browser_type`: 输入文本 "Hermes AI Agent" 
- `browser_click`: 点击Submit按钮
- 验证：页面更新为 "Submitted Form Data"

**结论：**
- 感知层(AX Tree 8ms) + 执行层(browser_click) 闭环成功
- Hermes可作为真人化AI Agent执行桌面任务
- 无需VLM兜底，CDP+AX Tree方案足够快且准

---

## 快眼 OCR（Apple Vision，原生极速）

三层感知的第一层：文字按钮用 Vision OCR 定位，60-240ms，零 GPU 消耗，比 VLM 快 4-5 倍。

### 安装依赖

```bash
~/.hermes/hermes-agent/venv/bin/pip install pyobjc-framework-Vision pyobjc-framework-Quartz
```

### 性能基准（M4 24GB，实测）

| 操作 | 耗时 | 备注 |
|------|------|------|
| CGWindowListCreateImage 全屏截图 | 87ms | 截图不含 OCR |
| Vision OCR 全屏（Fast级别） | 233ms | 68-92个文本块 |
| Vision OCR 局部（1/6屏） | 60ms | 已知目标区域时用 region 参数，3-4x 加速 |
| SSIM 对比（1920×1080） | 5ms | 极低开销 |

### 坐标转换关键坑

Vision 返回归一化坐标，原点在**左下角**。需转换：

```python
cx = (bbox.origin.x + bbox.size.width / 2) * screen_width
cy = (1 - bbox.origin.y - bbox.size.height / 2) * screen_height
```

### ⚠️ PaddleOCR `show_log` 参数已废弃（2026-06-01 实测）

新版本 PaddleOCR（pip安装的v3.x）已移除 `show_log` 参数，直接删除：

```python
# ❌ 旧写法（报错：Unknown argument: show_log）
ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

# ✅ 正确写法
ocr = PaddleOCR(use_angle_cls=True, lang='ch')
# 或完全省略
ocr = PaddleOCR()
```

### 已知局限

- 终端/TUI 渲染内容识别率低（字符集不标准）
- 对 1688/微信等高对比度网页效果显著更好
- OCR 找不到时自动 fallback 到 VLM

---

## 视觉心跳（SSIM 点击验证）

三层感知的验证层：点击前后截图跑 SSIM，5ms 判断是否真正跳转。

### SSIM 阈值（实测）

| SSIM 值 | 判定 | 含义 |
|---------|------|------|
| > 0.98 | `failed` | 画面几乎无变化，点击可能失效 |
| < 0.92 | `success` | 显著跳转，页面切换成功 |
| 0.92-0.98 | `uncertain` | 轻微变化，可能是弹窗或局部刷新 |

### 区分度验证

- 完全相同图：1.000
- 随机噪声图：0.007
- 1%像素变化：0.990

### 效果

把 VLM 从"确认点击结果"苦力中解放，用像素级对比做瞬断，零 Token 消耗。

### execute_code 沙箱注意

`execute_code` 使用的 venv 没有 pyobjc 模块。运行 Vision OCR 必须用：

```bash
/Users/aimac/.hermes/hermes-agent/venv/bin/python /tmp/your_script.py
```

或在脚本开头加 PATH 修复：

```python
import sys
venv_python = "/Users/aimac/.hermes/hermes-agent/venv/bin/python"
```

---

## 三层感知点击架构（推荐）

```
smart_click("发送")
    │
    ├─ 1. 局部截图 -> Vision OCR (60-240ms)
    │       找到了 -> human_click + SSIM 心跳验证
    │
    ├─ 2. 找不到 -> qwen3-vl:2b 视觉 (~2s)  [注意：qwen3-vl:latest太大已删，轻量模型优先]
    │       找到了 -> human_click + SSIM 心跳验证
    │
    └─ 3. VLM 也找不到 -> 打印警告，人工介入
```

> **注意**：smolvlm2 和 qwen3-vl:latest 均已删除。当前VLM为 qwen3-vl:2b (1.9GB)，M4 24GB可流畅运行。
>
> ⚠️ **内存警示**：qwen3-vl:latest (6.1GB) 会导致24GB Mac mini系统瘫痪（Ollama runner占用15GB RAM）。诊断方法：`top -l 1 | grep PhysMem`。Docker Linux VM只占~600MB，不是内存瓶颈。及时清理不需要的模型。

> ⚠️ **github blocked 期间**，FastVLM、SmolVLM2-2.2B、moondream2 等候选模型无法 pull 测试。网络恢复后优先测试 Apple FastVLM（CVPR 2025，85x faster TTFT，MLX版本在HuggingFace可用）。

## 新一代屏幕感知模型（2026-05 进展）

### UI-TARS-1.5-7B（ByteDance）— 最高优先级
- **OSWorld SOTA**：24.6@50步，超越 Claude Computer Use（22.0@50步）
- **架构**：端到端VLM（感知+推理+定位+记忆一体化），比 smolvlm2 的分离式更优
- **部署**：
  - Electron桌面应用（macOS支持）：UI-TARS Desktop
  - MCP server：`sandraschi/uitars-mcp`（★1）
  - vLLM本地部署：见 deepwiki.com/bytedance/UI-TARS/4.2-local-deployment
- **VRAM需求**：官方推荐RTX 4090级别，M4 24GB统一内存 borderline
- **行动**：测试UI-TARS Desktop macOS版，评估M4兼容性

### OmniParser v2.0（Microsoft）★24,823
- **能力**：纯视觉GUI解析器，截图→结构化元素
- **最新**：v2.0.1（2025-09-12），60%延迟改善
- **ScreenSpot Pro**：39.6% grounding准确率
- **定位**：分离式感知层，适合与smolvlm2组合使用
- **局限**：不是端到端agent，只是解析层

### ZonUI-3B（WACV 2026）— 轻量化方向
- **参数**：3B（RTX 4090单卡可训）
- **性能**：接近大型模型GUI grounding水平
- **意义**：M4 Mac可能可以流畅运行
- **状态**：研究阶段，关注进展

### 屏幕感知架构演进方向
```
现状（分离式）：
AX树(20ms) → 元素结构
  ↓ 失败时
Vision LLM smolvlm2(2-5s) → 语义理解 → 坐标输出

进化后（端到端）：
UI-TARS端到端(1-2s) → 直接操作指令
  或
OmniParser v2.0(500ms) → 结构化元素 → 更快解析
```

### 决策建议
| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| M4流畅运行 | ZonUI-3B（待验证） | 轻量化，3B参数 |
| 追求最强能力 | UI-TARS Desktop | OSWorld SOTA |
| 快速集成 | OmniParser v2.0 | 已有pip安装，延迟改善 |

分层感知原则：能用底层 API 解决的不上高级模型，日常 80% 点击走 OCR 瞬发。定位参考：`hermes-fast-ocr-ssim`
