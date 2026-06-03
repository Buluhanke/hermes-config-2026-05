# Mac OCR / 视觉识别方案 — 5站跨测综合知识库
## 来源：2026-06-03 ChatGPT / DeepSeek / ChatGLM / 豆包 / Gemini 5站并行回答

---

## 核心推荐组合（按优先级）

### 一线主力（24GB M4 无压力，< 200MB）

| 方案 | 类型 | 内存占用 | 精度 | 速度 | 调用方式 |
|------|------|---------|------|------|---------|
| Accessibility API | 界面读取 | ≈0 | ≈100% | 即时 | AXUIElementCopyAttributeValue |
| Apple Vision Framework | OCR | 极低 | ★★★★★ | 几十~200ms/张 | Swift VNRecognizeTextRequest |
| ocrtool-mcp | OCR+MCP | 极低 | ★★★★★ | 快 | JSON-RPC，MCP协议 |

### 二线补充（复杂场景）

| 方案 | 类型 | 内存占用 | 精度 | 速度 | 备注 |
|------|------|---------|------|------|------|
| uitag + YOLO | 图标+文字 | 低 | 90.8% | ~1s | pip install "uitag[yolo]" |
| EasyScreenOCR | OCR工具 | 低 | 高 | 快 | 菜单栏App，快捷键 |
| PaddleOCR | OCR引擎 | 中 | 高 | 中 | 支持表格/公式 |
| Tesseract | OCR引擎 | 低 | 中 | 中 | brew install tesseract |
| DeepSeek-OCR | 本地Web | 高 | 极高 | 慢 | MPS加速，适合复杂文档 |

---

## 分层读取策略（ChatGLM 方案，最优架构）

```
CDP DOM 读取
    ↓ 读不到
Accessibility API（直接读 AX 树，无需截图）
    ↓ 还读不到
Apple Vision OCR（本地截图识别）
    ↓ 最后手段
ocrtool-mcp / uitag（返回坐标）
```

**90%以上网页场景不需要截图OCR。**

---

## 关键工具详解

### Apple Vision Framework
- **优势**：M4 Neural Engine 优化，完全本地，中文支持，Apple 官方
- **调用**：`VNRecognizeTextRequest` + `CGWindowListCreateImage` 截图
- **Swift 示例**：见 ChatGLM 回复原文
- **Python**：via PyObjC + Vision 框架

### ocrtool-mcp
- **优势**：开源，Swift+Vision，MCP 协议，返回结构化坐标
- **安装**：`chmod +x ocrtool-mcp && ./ocrtool-mcp`
- **返回格式**：`{"text":"登录","x":123,"y":456}`

### uitag
- **优势**：唯一同时识别文字+图标的方案
- **命令**：`uitag screenshot.png --yolo -o ./output`
- **YOLO 加持**：准确率从 57.3% → 90.8%

### EasyScreenOCR
- **授权**：需在「系统偏好设置 > 隐私与安全性 > 屏幕录制」授权
- **限制**：免费版批量>5张才有专业版限制，日常够用

---

## 已知限制

- **Accessibility API**：仅适用于支持无障碍接口的 App（Chrome/Safari 支持良好）
- **Vision Framework**：不做视觉理解，只做文字识别；手写/艺术字效果有限
- **本地 VLM**（Qwen2-VL/LLaVA/MLX-VLM）：适合图文混合理解，24GB 可运行但资源占用高
- **DeepSeek-OCR**：配置复杂，适合学术文档/扫描版PDF

---

## M4 性能参考
- Vision OCR：几十毫秒~200毫秒/张（A4），M4 比 M1 快（ M1 ~8.2秒/张A4）
- 内存占用：全程 < 200MB，Neural Engine 承担推理