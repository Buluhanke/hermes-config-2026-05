# Hermes 系统配置审计 2026-05-16

## 硬件与系统
- Mac mini M4 24GB / macOS 26.4.1
- IPv6: 240e:390:6ec3:f0:447a:c0b2:21ab:bf24

## 对话模型（已配置）
- MiniMax-M2.7 主用（直连 https://api.minimaxi.com/anthropic）
- MiniMax-M2.7-highspeed 备用（V2.aicodee.com中转）
- deepseek-v4-flash 备用

## 工具层
- 视觉：provider=auto
- TTS：edge + elevenlabs + xai + neutts + piper
- MCP：chrome-mcp（stdio，31工具）
- 浏览器：Chrome调试端口9333 + mcp-chrome-stdio混合架构

## Skills（50+个）
核心真人化：hermes-humanization-core、hermes-vision-agent、hermes-voice-module、hermes-memory-hpc

## 真人化卡点（三家AI汇总）
| 卡点 | 程度 | 免费方案 |
|------|------|---------|
| 屏幕全域感知 | 95%缺 | Qwen3-VL-7B + Ollama + browser-use |
| 移动端 | 100%盲区 | Telegram Bot桥接（最快） |
| 验证码 | 100%卡点 | 2Captcha API兜底 + PaddleOCR |
| 情绪感知 | 缺 | 待攻克 |

## 优先突破路线（三家一致）
1. 先跑通browser-use（AI可控浏览器）
2. 内存建议：24GB用Qwen2.5-VL-7B Q4量化先验证
3. 移动端：Telegram Bot低成本突破
4. 验证码：远程API过渡

## 安装命令
```bash
brew install ollama
ollama pull qwen2.5-vl:7b
pip install browser-use
npx @modelcontextprotocol/server-playwright
```