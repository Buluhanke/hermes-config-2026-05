# Vocaela-500M 基准与集成方案

> 发现日期：2026-05-29，来源：HuggingFace blog + HF model page
> 模型：vocaela/Vocaela-500M（GGUF: vocaela/Vocaela-500M-GGUF）
> 类型：GUI Agent 专用 VLM，输出结构化 JSON action

## 关键指标

| 指标 | Vocaela-500M | smolvlm2-agentic-gui (当前) | 差异 |
|------|-------------|---------------------------|------|
| 参数 | 500M | 2.2B | **4.4x 更小** |
| Size (GGUF) | 437 MB + 109 MB mmproj | 1.85 GB (Q4_K_M) | **3.4x 更小** |
| ScreenSpotV2 | **85.8%** | 61.71% | **+24pp** |
| 输出格式 | 结构化 JSON action | 自由文本 | **更易解析** |
| 坐标格式 | 归一化 [0,1) | 文本描述 | **更精确** |

## ScreenSpotV2 全维度

| 维度 | Vocaela-500M | smolvlm2 (2.2B) |
|------|-------------|-----------------|
| Mobile-Text | 95.9% | - |
| Mobile-Icon | 73.93% | - |
| Desktop-Text | 95.4% | - |
| Desktop-Icon | 75.7% | - |
| Web-Text | 91.0% | - |
| Web-Icon | 75.4% | - |
| **Overall** | **85.8%** | **61.71%** |

## 与其他小模型对比（<=4B, ScreenSpotV2）

| 模型 | Size | Score |
|------|------|-------|
| Vocaela-500M | **500M** | **85.8%** |
| OS-Atlas-4B | 4B | 68.5% |
| ShowUI-2B | 2B | 77.3% |
| Phi-Ground-4B | 4B | 84.1% |
| TongUI-3B | 3B | 85.5% |
| Holo1.5-3B | 3B | 91.7% |

## Action Space

Vocaela-500M 支持的动作类型与 hermes-rpa 高度一致：

| Action | 参数 | 对应 hermes-rpa |
|--------|------|----------------|
| click | coordinate [0,1) | human_click |
| type | text | human_type |
| mouse_move | coordinate [0,1) | human_move |
| drag | coordinate, coordinate2 | drag |
| right_click | coordinate | human_right_click |
| double_click | coordinate | double click |
| scroll | scroll_direction (up/down) | human_scroll |
| press_key | key + presses | pyautogui.press |
| hotkey | hotkeys[] | pyautogui.hotkey |

## 限制

1. **低分辨率限制**：model 设计最长边 2048px，ScreenSpotPro (高分辨率大屏+小按钮) 仅 15.1%
2. **无通用对话/推理能力**：纯 GUI agent 模型，不适合问答/聊天场景
3. **输出格式固定**：不支持自由文本描述，只输出 JSON action
4. **依赖 mmproj**：需要独立的 multimodal projector GGUF（109MB）

## 集成方式

### Ollama（推荐）
```bash
ollama run hf.co/vocaela/Vocaela-500M-GGUF:Q8_0
```
⚠️ `hf.co` 语法需要 Ollama >= 0.19.x；如不兼容，用 llama.cpp 方式

### llama.cpp
```bash
brew install llama.cpp
llama-cli -hf vocaela/Vocaela-500M-GGUF:Q8_0
```

### 下载 GGUF（github blocked 时走 HF 镜像）
```bash
# 镜像已验证可达 (302 redirect)
curl -L -o Vocaela-500M-Q8_0.gguf \
  "https://hf-mirror.com/vocaela/Vocaela-500M-GGUF/resolve/main/Vocaela-500M-Q8_0.gguf"
curl -L -o mmproj-Vocaela-500M-Q8_0.gguf \
  "https://hf-mirror.com/vocaela/Vocaela-500M-GGUF/resolve/main/mmproj-Vocaela-500M-Q8_0.gguf"
```

### Vocaela-2（更新版本）
```bash
ollama run hf.co/vocaela/Vocaela-2-500M-1024R2
```
声称 3x faster，支持更高分辨率。
