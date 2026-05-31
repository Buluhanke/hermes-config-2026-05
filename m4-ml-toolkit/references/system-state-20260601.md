# 系统能力状态快照（2026-06-01）

## 当前架构

```
hermes-agent (gateway, Telegram主渠道)
├── holographic (记忆插件, memory_store.db)
├── chromadb (原生uvicorn, 端口8000)
├── mcp_chrome (浏览器自动化, 9333端口)
├── je_auto_control (AX树控制)
├── playwright (浏览器自动化)
└── cron jobs (7个定时任务)
```

## 正常工作的能力

| 能力 | 工具 | 状态 |
|------|------|------|
| 对话 | MiniMax API (V2.aicodee.com) | ✅ |
| 视觉备用 | Gemini | ✅ |
| 浏览器自动化 | mcp_chrome + playwright | ✅ |
| 电脑控制 | je_auto_control + cua | ✅ |
| 记忆系统 | holographic + chromadb原生 | ✅ |
| 联网搜索 | ddgs (DuckDuckGo) | ✅ |
| YOLO检测 | ultralytics (venv) | ✅ |
| OCR | PaddleOCR (系统Python) | ✅ |
| 定时任务 | cronjob | ✅ |

## 已删除/不依赖的工具

| 工具 | 之前状态 | 当前状态 |
|------|----------|----------|
| Docker/Colima | 运行 | **已删除** |
| Ollama app | 运行 | **已卸载** |
| hindsight (Docker) | 运行 | **已废弃，改用holographic** |
| SearXNG (Docker) | 运行 | **已删除，无替代** |
| n8n (Docker) | 运行 | **已删除** |
| open-webui (Docker) | 运行 | **已删除** |

## 当前安装的pip包（系统Python 3.14）

```
ddgs ✅ (DuckDuckGo搜索)
playwright ✅ (1.58.0, chromium已装)
cua ✅ (0.1.0)
je-auto-control ✅ (0.0.192)
ultralytics ✅ (YOLOv8)
paddleocr ✅ (3.6.0)
easyocr ✅ (1.7.2)
torch ✅ (2.12.0, MPS可用)
torchvision ✅ (0.27.0)
onnxruntime ✅ (1.26.0)
```

## 模型路由（当前）

- **Primary**: deepseek-v4-flash via V2.aicodee.com
- **Fallback 1**: MiniMax-M2.7-highspeed via custom
- **Fallback 2**: deepseek-v4-flash via deepseek直连

## 内存状态

- 总: 24GB
- 空闲: ~17GB (Ollama已卸载后)
- 主要进程: hermes-agent (~250MB), chromadb (~300MB)

## API配置

- 所有key在 `~/.hermes/.env`
- config.yaml通过 `api_key_env` 引用.env
- 已删除Groq/Cerebras等失效provider
