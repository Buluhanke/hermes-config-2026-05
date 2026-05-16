# Consultation Example: Hermes 真人化方案

## 背景
用户：义乌市迅龙贸易公司老板
问题：Hermes Agent（Mac mini M4 24GB）如何从对话模型进化为数字生命体
约束：免费/低成本、本地运行优先
当前状态：已配置 MiniMax-M2.7-highspeed（aicodee中转）+ deepseek-v4-flash

## 简报文件（发给AI的共同输入）
见 ai-consult-prompt.md — 包含完整系统审计摘要和6个具体问题

## 角色配置

| 角色 | context 开头 | 专长 |
|------|-------------|------|
| 智谱清言 | 你是智谱清言（GLM）的AI语言模型代表... | 国产方案、免费API |
| GPT | 你是GPT (OpenAI) 的AI专家... | 全球生态、开源方案 |
| DeepSeek | 你是DeepSeek的AI专家... | 推理模型、本地部署 |

## 输出结构示例

### 三家AI共识（全部一致推荐）
1. 装 atomacos + 配 Google Gemini 免费API（最快破局点）
2. 开启 auto_tts + edge-tts 切中文voice（立竿见影）
3. 注册 DeepSeek API 免费额度（500万token）

### 各家独特见解
- 智谱清言：推荐 CosyVoice 2 情感TTS，三层感知架构
- GPT：推荐 Qwen2.5-VL 7B 本地跑，SSIM像素验证
- DeepSeek：反对跑本地VL（M4 24GB太慢），推荐纯Gemini API

### 分阶段路线图（合并）
Phase 0（今天·2小时·0元）→ Phase 1-2（1周）→ Phase 3（1月）

## 关键教训
- 角色差异化是关键——三个角色给相同context会导致雷同
- 冲突点是精华——DeepSeek坚持"不要跑本地VL"和GPT推荐"装Ollama+VLM"的差异本身就是有价值的
- 简报文件不要超过2000字——太长子agent会读不完
