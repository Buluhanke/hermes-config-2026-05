# browser-use + Gemini 集成记录（2026-05-30）

## 结论

browser-use 0.12.8 与 Gemini（通过 langchain-google-genai 的 ChatGoogleGenerativeAI）**不兼容**。

## 症状

- 第1步导航正常（通过 Agent 预置的初始 action 完成）
- 第2步开始失败：`Unsupported message type: <class 'browser_use.llm.messages.SystemMessage'>`
- Gemini 不识别 browser-use 自定义消息类型（SystemMessage/HumanMessage 等都用 browser_use.llm.messages 而非 langchain 标准类型）

## 已应用的补丁

browser-use 0.12.8 在系统 Python 3.14 环境有6处 `llm.provider`/`model_name` AttributeError 修复：

1. `tokens/service.py:347` — `llm.provider` → `getattr(llm, 'provider', 'unknown')`
2. `tokens/service.py:389` — `llm.provider == 'openrouter'` → `getattr(...)`
3. `agent/service.py:1603` — `self.judge_llm.provider == 'browser-use'` → `getattr(...)`
4. `agent/service.py:2044` — f-string `self.llm.provider` → 变量 proxy
5. `agent/service.py:2210` — `model_provider=self.llm.provider` → `getattr(...)`
6. `agent/cloud_events.py:217` — `agent.llm.model_name` → `getattr(..., 'model_name', agent.llm.model)`

## 根本原因

browser-use 0.12.8 使用：
- 自定义消息类型（browser_use.llm.messages.*）
- `output_format` kwarg 透传给 `ainvoke()`（仅 ChatBrowserUse 支持）
- 期望 `response.completion` 存在（仅 ChatBrowserUse 的 structured output）

标准 LangChain 模型（ChatGoogleGenerativeAI）不兼容这三项。

## 可选的解决方案

1. **升级 browser-use 到 0.12.9** — 可能有兼容性修复
2. **用 OpenAI/Anthropic 模型驱动** — browser-use 原生支持
3. **Playwright CDP 备份脚本** — `~/.hermes/scripts/browser_cdp.py`，Hermes 自己做决策+执行
4. **不经过 browser-use，直接用 Playwright CDP + LLM** — Hermes 自己当大脑

## 当前推荐

方案3：Playwright CDP 备份脚本已可用且稳定连接 `localhost:9333`。
