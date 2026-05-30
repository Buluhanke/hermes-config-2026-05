# 6个AI专家网站真人化建议汇总（2026-06-01）

## 调研方法
同时向6个AI网站发送同一问题（通过Playwright CDP批量操作）：
> "推荐当下最好最智能的browser自动化方案给Hermes AI Agent，可结合本地模型"

## 各平台回复

| 平台 | 状态 | 字数 | 核心建议 |
|------|------|------|----------|
| DeepSeek | ✅ | 6946 | Steel云浏览器 + Browse.sh 250+技能 |
| Gemini | ✅ | 1646 | Browser-Use + Stagehand + OmniParser |
| 豆包 | ✅ | 3828 | Browser-Use + Qwen3-V-14B本地VLM |
| ChatGPT | ✅ | 2316 | Stagehand + Playwright + Qwen3 8B |
| ChatGLM | ✅ | 2388 | CrewAI + Playwright + 本地LLM |
| Grok | ⚠️ | 585 | 加载慢，未成功发送 |

## 跨平台共识

| 方案 | 推荐次数 | 来源 |
|------|---------|------|
| Browser-Use + Playwright | 4次 | DeepSeek/Gemini/豆包/ChatGLM |
| Stagehand | 2次 | Gemini/ChatGPT |
| CrewAI | 1次 | ChatGLM |
| Steel/Camofox（反爬） | 2次 | DeepSeek/豆包 |
| 本地VLM（Qwen3） | 4次 | 全部推荐本地模型 |

## 落地优先级

1. **Browser-Use** — 多平台一致推荐，GitHub 91K stars，v0.12.8已装
2. **Playwright CDP直连** — 已有browser_cdp.py，完全可用
3. **Stagehand** — act/extract/observe三API，比Browser-Use轻量
4. **CrewAI** — 多Agent编排，适合复杂任务

## 关键发现：Browser-Use + ChatOllama 兼容性

**问题**：Browser-Use检查 `llm.provider == 'browser-use'` 但 ChatOllama 没有 `provider` 属性。

**Python 3.14路径**（browser-use 3.14 site-packages）：
```
/usr/local/bin/python3.14
/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/
```

**修复（1行patch）**：
```python
# browser_use/agent/service.py 第235行
# 原：if llm.provider == 'browser-use':
# 改：if getattr(llm, 'provider', None) == 'browser-use':
```

**安装langchain-ollama**：
```bash
python3.14 -m pip install langchain-ollama  # 已装 v1.1.0
```

## AI网站登录状态（2026-06-01）

| 平台 | 状态 | 备注 |
|------|------|------|
| ✅ DeepSeek | 可用 | 完整回复 |
| ✅ 豆包 | 可用 | chrome-debug已登录 |
| ✅ Gemini | 可用 | 免登录 |
| ✅ ChatGPT | 可用 | 用户手动登录 |
| ✅ ChatGLM | 可用 | 需滑动验证但已通过 |
| ✅ Grok | 可用 | 用户登录后可用 |

## AI专家咨询方法论

**免登录三站**（推荐优先使用）：
1. **Gemini** — gemini.google.com，免登录，多模态强
2. **豆包** — doubao.com，免登录，字节跳动，响应快

**需要登录**：
- DeepSeek（手机验证码）、ChatGPT（cookies）、Grok（注册）
- ChatGLM（滑动验证）

**Chrome双Profile隔离**：
- browser工具专用：`~/.hermes/chrome-debug/`
- 用户日常Chrome：`~/Library/Application Support/Google/Chrome/Default/`
- 两者Cookie不共享，需分别登录