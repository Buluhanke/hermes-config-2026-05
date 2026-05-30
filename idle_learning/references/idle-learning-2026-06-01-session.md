# Idle Learning Session — 2026-06-01

## 执行摘要

用户要求：完成昨夜深度学习任务 + 多平台AI网站检查。

## 完成工作

### 1. 豆包多平台AI调研
- 归档：`~/Brain_Lab/ai_agent_human_like_skills.md`（多平台调研报告）
- Gemini：✅ 已登录，获取完整真人化建议（快慢双回路、SeeClick/YOLO、CoreML优化）
- 豆包：⚠️ 已登录，但未见回复
- 智谱GLM/DeepSeek/ChatGPT/Grok：登录状态各异（详见 `embodied-agent-evolution/references/ai-websites-multi-profile-20260601.md`）

### 2. 关键发现

**Chrome双Profile隔离（2026-06-01修正）**：
- browser工具的Chrome（chrome-debug）与用户日常Chrome（Default）是**两个独立Profile**
- cookies不共享，导致AI网站登录状态不一致
- 解决方案：在chrome-debug中完成登录授权

**PaddleOCR `show_log` 参数废弃（2026-06-01实测）**：
- 新版本PaddleOCR已移除`show_log`参数
- 错误写法：`PaddleOCR(show_log=False)` → `ValueError: Unknown argument: show_log`
- 正确写法：`PaddleOCR()` 或 `PaddleOCR(use_angle_cls=True, lang='ch')`

## Skills更新

| Skill | 更新内容 |
|-------|---------|
| `embodied-agent-evolution` | Chrome双Profile架构修正 + 新reference `ai-websites-multi-profile-20260601.md` |
| `hermes-vision-agent` | PaddleOCR `show_log` 废弃说明 |
| `idle_learning` | AI专家网站清单修正（智谱清言/DeepSeek需登录） |
