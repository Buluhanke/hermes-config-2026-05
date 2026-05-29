# UI-TARS Desktop 执行层调研

## 基本信息
- **项目**：bytedance/UI-TARS-desktop（35.6k stars）
- **架构**：Electron桌面应用 + Agent TARS CLI
- **定位**：纯视觉桌面Agent，可操作电脑/浏览器/手机界面
- **最新版本**：v0.3.0（Agent TARS CLI），支持多工具流式执行 + 运行时统计

## 操作模式（4种）
1. **Local Computer**：NutJS驱动鼠标/键盘，本地截屏 + VLM理解
2. **Local Browser**：Puppeteer浏览器自动化，本地处理
3. **Remote Computer**：云端虚拟电脑，30分钟免费试用，VNC预览
4. **Remote Browser**：云端浏览器自动化，30分钟免费试用

## VRAM需求（UI-TARS-7B）
| 量化 | VRAM | 模型大小 |
|------|------|----------|
| FP32 | ~28GB | ~33GB |
| FP16 | ~14-16GB | ~15.2GB |
| Q8_0 | ~8GB | ~8.1GB |
| Q6_K | ~6.5GB | ~6.25GB |
| Q4_K_S | ~4.5GB | ~4.46GB |
| Q2_K | ~3.5GB | ~3.02GB |

**M4 24GB推荐**：Q4_K_S量化版（~4.5GB VRAM），可用Q4_K_S在Ollama/vLLM运行

## Mac安装方式
```bash
# 直接下载（推荐）
# 下载 .dmg（Apple Silicon版 for M1-M4）
# 拖到 Applications 文件夹

# Homebrew
brew install --cask ui-tars
```

### 权限配置（必须）
- **无障碍权限**：系统设置 → 隐私与安全性 → 无障碍 → 添加 UI-TARS
- **屏幕录制权限**：系统设置 → 隐私与安全性 → 屏幕录制 → 添加 UI-TARS

## VLM后端配置
支持3种VLM provider：
1. **HuggingFace Inference Endpoints**（云端）
2. **VolcEngine**（字节豆包云）
3. **OpenAI兼容端点**（Ollama、vLLM等）

### Ollama配置示例
- Base URL: `http://localhost:11434/v1`
- API Key: 任意值（如 `local`）
- Model: `qwen3-vl:4b` 或 `llama3.2-vision:11b`

## 架构亮点
```
截图 → VLM理解 → 动作规划 → NutJS执行 → 验证结果
```
闭环架构与ScreenAgent一致，vision→action→verify循环。可作为hermes auto_execute参考。

## NutJS vs cliclick
| 特性 | NutJS | cliclick |
|------|-------|----------|
| 用途 | UI-TARS自动化 | Hermes自动化 |
| 平台 | 跨平台 | macOS专用 |
| 语言 | Node.js | CLI工具 |
| 坐标 | 像素坐标 | 像素坐标 |

## 已知Bug
- **Mac M4 Pro截图全白**（Issue #1794，Jan 2026）：截屏后PNG全白，可能与macOS截图API有关
- **解决方案**：暂无官方修复，可能需要调整截屏方式或等待更新

## 与Hermes对比
| 维度 | UI-TARS Desktop | Hermes |
|------|----------------|--------|
| 视觉模型 | UI-TARS专用VLM | smolvlm2/Qwen3-VL |
| 自动化层 | NutJS | cliclick |
| 执行方式 | Electron桌面应用 | CLI + cron |
| 本地运行 | 需要16GB+ VRAM | M4 24GB可跑 |
| 定制化 | 低 | 高（完全可控） |

## 核心价值
- **94.2%** ScreenSpot-V2 坐标准确率（smolvlm2 的 61.71%）
- UI-TARS 2 MoE 达 **47.5%** OSWorld（2x Claude Computer Use）
- 闭环架构验证了"vision→action→verify"范式的可行性
- NutJS作为自动化层的成熟度验证，可作为hermes-rpa的替代参考