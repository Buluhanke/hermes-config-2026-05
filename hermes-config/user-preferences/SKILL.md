---
name: user-preferences
description: 用户偏好和配置记忆
---
# 用户配置记忆

## 五大AI网站（用户定义）
用户说"几大模型网站/几大AI网站/几大网站"均指这5个：
1. https://chatgpt.com/ （ChatGPT）
2. https://chat.deepseek.com/ （DeepSeek）
3. https://grok.com/ （Grok/xAI）
4. https://chatglm.cn/main/alltool?lang=zh （ChatGLM/智谱AI）
5. https://gemini.google.com/app?hl=de （Google Gemini）

## 知识吸取方式
- 五大多已登录本地Chrome（端口9333）
- 可通过Chrome导航到这些网站获取实时知识
- 优先用浏览器直接查，而非依赖模型记忆

## 模型链顺序（2026-05-17确认）
1. `V2.aicodee.com/MiniMax-M2.7-highspeed` — 中转MiniMax（主模型）
2. `minimax-cn/MiniMax-M2.7` — 直连MiniMax（Fallback 1）
3. `deepseek/deepseek-v4-flash` — DeepSeek（Fallback 2）
provider: custom，base_url: https://v2.aicodee.com/v1

## Auth-to-Enable 认知缺口
**授权 ≠ 启用**。Portal/`hermes auth` 只写认证（`.env`），不改默认模型（`model.default`）。授权后必须在 config.yaml 显式设置 `model.default` 才能在实际对话中使用该模型。详见 `hermes-agent/references/channel-model-management.md` 的 Auth-to-Enable Pipeline 章节。

## 沟通风格
- 极端简短，积极配合
- 命令审批提示必须用中文（不能用英文）
- 不需要请示，直接判断执行
- 全程中文

## Terminal自动化限制（macOS）
macOS安全限制：osascript无法自动向Terminal发送命令（do script会超时）。正确做法：
1. 创建 .command 文件：写入脚本内容 + chmod +x
2. 手动双击运行，或告知用户手动执行
3. osascript/automation无法绕过此限制