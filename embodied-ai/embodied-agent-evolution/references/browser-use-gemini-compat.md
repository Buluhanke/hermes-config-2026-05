# browser-use 与 LangChain 模型兼容性

## 问题描述
browser-use 0.12.8 不能直接与 `ChatGoogleGenerativeAI`（Gemini via LangChain）配合使用。

### 第1层问题：AttributeError: 'provider'
browser-use 内部多处直接访问 `llm.provider` 和 `llm.model_name`，但 LangChain 标准 LLM 对象没有这些属性。

**已打6处patch修复（系统Python 3.14版本）：**
```python
# 所有 llm.provider → getattr(llm, 'provider', None)
# 所有 llm.model_name → getattr(llm, 'model_name', llm.model)
```

涉及文件：
- `browser_use/agent/service.py` — 4处
- `browser_use/agent/cloud_events.py` — 1处
- `browser_use/tokens/service.py` — 2处

### 第2层问题：自定义消息类型
browser-use 使用 `browser_use.llm.messages.SystemMessage` 等自定义消息类型，Gemini 的 `ChatGoogleGenerativeAI` 无法识别，报：
```
Unsupported message type: <class 'browser_use.llm.messages.SystemMessage'>
```
这发生在第2步——第1步导航可以通过初始action执行，但第2步开始模型调用需要解析上下文消息时失败。

### 第3层问题：kwargs透传
browser-use 向 `llm.ainvoke()` 传 `output_format` 和 `session_id` 参数，这些不是标准 LangChain 参数。已修复——仅对 `ChatBrowserUse` 传 `output_format`。

## 结论
browser-use 0.12.8 底层消息系统是为 OpenAI/Anthropic API 设计的。用 Gemini 驱动需要：
1. 升级 browser-use 到兼容版本（尝试 0.12.9）
2. 或换用 OpenAI/Anthropic 模型
3. 或绕开 browser-use 直接用 Playwright CDP + 我（Hermes）做决策
