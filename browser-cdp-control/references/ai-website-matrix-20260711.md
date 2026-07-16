# AI 网站矩阵（2026-07-11 已全部登录验证）

## 11个已登录AI网站

| 站点 | URL | 用途 |
|------|-----|------|
| Gemini | https://gemini.google.com/app | 搜索、对话、多模态 |
| 豆包 | https://www.doubao.com/chat | 中文对话、内容分析 |
| 智谱GLM | https://chatglm.cn/main/alltoolsdetail | 中文推理、图表生成 |
| DeepSeek | https://chatdeepseek.com/ | 深度推理、代码 |
| ChatGPT | https://chatgpt.com/ | 通用对话、插件生态 |
| Grok | https://grok.com/ | 实时信息、幽默风格 |
| Claude | https://claude.ai/ | 长文本分析、写作 |
| 文心一言 | https://yiyan.baidu.com/ | 中文生成、百度生态 |
| Kimi | https://kimi.moonshot.cn/ | 超长上下文、文件分析 |
| 讯飞星火 | https://xinghuo.xfyun.cn/ | 语音交互、垂直场景 |
| 备用 | https://wtxl.xai6.com/ | 备选平台 |

## 使用方法

```
browser_navigate → 输入查询 → browser_vision截图分析
```

不要依赖 `vision_analyze`（不支持 file:// URL），用 `browser_vision` 自己截图分析。

## 批量打开（单命令）
```bash
open -a "Google Chrome" https://gemini.google.com/app \
  https://www.doubao.com/chat \
  https://chatglm.cn/main/alltoolsdetail \
  https://chat.deepseek.com/ \
  https://chatgpt.com/ \
  https://grok.com/ \
  https://claude.ai/ \
  https://yiyan.baidu.com/ \
  https://kimi.moonshot.cn/ \
  https://xinghuo.xfyun.cn/
```

## 深度研究触发词
「深度研究」「详细调研」「多引擎搜索」「深入分析」→ 触发 deep-research skill（Search→Extract→Verify→Report 完整闭环）

## OCR 降级链（所有 CDP/vision 工具失效时）
```
CDP Page.captureScreenshot → base64 decode → tesseract OCR
```
详见 `references/doc-weixin-ocr-read.md`
