# AI平台多网站真人化调研（2026-06-01）

## 平台访问状态（chrome-debug profile）

| 平台 | 状态 | 备注 |
|------|------|------|
| ✅ 豆包 | 可用 | 已有对话历史 |
| ✅ DeepSeek | 可用，已回复 | 最详细方案 |
| ✅ Gemini | 可用 | 已登录 |
| ✅ ChatGPT | 可用 | 已登录 |
| ✅ Grok | 可用 | 已登录 |
| ✅ ChatGLM | 可用 | 已登录 |
| ⚠️ 智谱GLM | 滑动验证 | chrome-debug中需滑动验证 |

## DeepSeek三条路径（最详细）

### 路径一：开箱即用（@hasna/computer）
- `bun install -g @hasna/computer`
- `computer run "打开Safari搜索..."`
- 核心：Bun + cliclick（macOS原生点击）
- 免费方案：配合Ollama + Qwen2.5-VL

### 路径二：本地隐私（Mano-P + Qwen）
- Mano-P：OSWorld榜单第一，M4优化，数十步复杂任务
- Qwen2.5-VL：Ollama本地运行
- je_auto_control执行 + Qwen分析

### 路径三：开发者控制（je_auto_control）⭐已落地
- AX元素定位（比视觉更准）
- OCR文字识别（Tesseract）
- 远程桌面流媒体
- **核心代码**：
```python
import je_auto_control as auto
auto.locate_and_click('确认')  # OCR找字+点击
```

## je_auto_control安装验证（2026-06-01）

```
pip3 install je-auto-control  # 成功，version 0.0.192
```

已安装完整pyobjc框架（pyobjc 12.1），包含：
- pyobjc-framework-Accessibility
- pyobjc-framework-Vision
- pyobjc-framework-CoreML
- pyobjc-framework-Metal
等全套macOS原生API

## 落地优先级

| 优先级 | 方案 | 工具 | 状态 |
|--------|------|------|------|
| P0 | je_auto_control | AX树+截图+鼠标键盘 | ✅ 已安装 |
| P0 | Playwright CDP | 浏览器DOM+点击 | ✅ 已验证 |
| P0 | cliclick | macOS原生点击 | ✅ 已安装 |
| P1 | @hasna/computer | 开箱即用Agent | 待测试 |
| P2 | Mano-P | M4优化GUI-VLA | 未开源 |
