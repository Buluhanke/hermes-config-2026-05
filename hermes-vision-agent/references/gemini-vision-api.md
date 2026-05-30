# Gemini API 视觉分析 — aistudio.google.com API Key 用处

## API Key 本质

aistudio.google.com API Key = Google AI Studio API Key = Gemini 模型 API

支持的模型（2026-06实测）：
- `gemini-2.5-flash` — 主推荐，100万token上下文，支持视觉
- `gemini-2.5-pro` — 最强推理，100万token

## Hermes 配置（已生效）

```yaml
auxiliary:
  vision:
    provider: gemini
    model: gemini-2.5-flash
    base_url: https://generativelanguage.googleapis.com/v1beta
    api_key: ''  # 从 GEMINI_API_KEY 环境变量读取
    timeout: 120
```

环境变量已配置：`GEMINI_API_KEY=***`（在 `~/.hermes/.env`）

## 测试命令

```bash
# 截图
screencapture -x /tmp/screen.jpg

# API Key 从 .env 读取
IMG_B64=$(base64 -b 0 < /tmp/screen.jpg)
PAYLOAD='{"contents":[{"parts":[{"text":"描述屏幕内容"},{"inlineData":{"mimeType":"image/jpeg","data":"'"$IMG_B64"'"}}]}]}'

curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d @/tmp/payload.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['candidates'][0]['content']['parts'][0]['text'])"
```

## Gemini vs 本地 VLM

| 维度 | Gemini 2.5 Flash | qwen3-vl:2b (Ollama) |
|------|-----------------|---------------------|
| 能力 | 强（Google最强小模型） | 中等（M4流畅运行） |
| 费用 | 吃API额度 | 免费离线 |
| 延迟 | ~2-3s | ~2s |
| 内存占用 | 无（云端） | 1.9GB RAM |
| 离线可用 | ❌ | ✅ |

## 建议用法

- 日常屏幕分析：qwen3-vl:2b（免费）
- 高精度需求：切Gemini 2.5 Flash（强20倍）
- Hermes vision工具自动走 `auxiliary.vision.provider` 配置，无需手动切换

## 已知限制

- API额度有限（Google AI Studio免费版有配额）
- 需要网络连接
- browser-use 不支持接入此API（独立SaaS，模型固定）