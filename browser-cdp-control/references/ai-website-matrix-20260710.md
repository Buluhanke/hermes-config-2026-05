# AI 网站矩阵（2026-07-10 已登录验证）

所有 11 个 AI 网站已通过 Chrome 登录，可随时通过 CDP 浏览器控制进行对话。

## 站点列表

| # | URL | 名称 | 验证状态 |
|---|-----|------|---------|
| 1 | https://gemini.google.com/app | Gemini (Google) | ✅ 已登录 |
| 2 | https://www.doubao.com/chat | 豆包 | ✅ 已登录 |
| 3 | https://chatglm.cn/main/alltoolsdetail | 智谱 GLM | ✅ 已登录 |
| 4 | https://chat.deepseek.com/ | DeepSeek | ✅ 已登录 |
| 5 | https://chatgpt.com/ | ChatGPT | ✅ 已登录 |
| 6 | https://grok.com/ | Grok | ✅ 已登录 |
| 7 | https://claude.ai/ | Claude | ✅ 已登录 |
| 8 | https://yiyan.baidu.com/ | 文心一言 | ✅ 已登录 |
| 9 | https://kimi.moonshot.cn/ | Kimi (月之暗面) | ✅ 已登录 |
| 10 | https://xinghuo.xfyun.cn/ | 讯飞星火 | ✅ 已登录 |
| 11 | https://wtxl.xai6.com/ | 备用 | ✅ 已登录 |

## 用途

- **多引擎交叉验证**：同一问题同时问 2-3 个 AI，取最优答案
- **获取最新知识**：各平台更新速度不同，Gemini/ChatGPT 最快
- **对比模型能力**：不同任务选最适合的模型

## 使用方法

```python
# 通过 CDP 打开并对话
browser_navigate(url)           # 打开网站
browser_click(ref)             # 点击输入框
browser_type(ref, "问题")      # 输入问题
browser_press(key="Enter")     # 发送
# 等待 15-25 秒（深度思考模式更久）
# 用 AX tree 或 Tesseract OCR 读取回复
```

## 并行采集策略

**不要**同时开多个标签页（browser_navigate 会覆写当前 tab）。正确方式：**串行处理**。

```
1. DeepSeek → 问 → 等 → 读 → 完成
2. Kimi → 问 → 等 → 读 → 完成
3. Gemini → 问 → 等 → 读 → 完成
```

并行节省的是"你等待回复的时间"，不是"打开网页的时间"。每个问题都要等 15-25 秒。

## 各站特点

| 站点 | 强项 | 回复速度 | 备注 |
|------|------|---------|------|
| Gemini | 实时信息、Google 生态 | 快 | 有深度思考模式 |
| DeepSeek | 推理能力强、中文好 | 中 | 有"快速/专家/图像识别"模式 |
| ChatGPT | 通用能力强、插件生态 | 快 | Plus 用户可联网 |
| Claude | 长上下文、安全性 | 中 | 适合长文分析 |
| 豆包 | 中文创意写作 | 快 | 字节跳动 |
| Kimi | 超长上下文(20万字) | 中 | 月之暗面 |
| 智谱 GLM | 中国政策/商业 | 中 | 清华出身 |
| 文心一言 | 百度搜索增强 | 快 | 依赖百度搜索 |
| 讯飞星火 | 语音交互 | 快 | 科大讯飞 |
| Grok | 幽默回答、实时 | 快 | xAI |
