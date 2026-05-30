# browser-use + Google Generative AI (Gemini) 集成

## 环境

- browser-use 0.12.8（系统pip + uv安装）
- Gemini 2.5 Flash API（Google AI Studio）
- Mac mini M4 24GB + macOS 26.4.1

## 依赖安装

```bash
# langchain-google-genai（Gemini的LangChain集成）
uv pip install langchain-google-genai --system

# CDP SOCKS代理支持
uv pip install python-socks --system

# Playwright浏览器（Browser-Use默认需要）
# 已安装：chromium-1208/1217/1223
```

## 已知Bug：AttributeError 'provider' / 'model_name'

browser-use 0.12.8 直接访问 `llm.provider` 和 `agent.llm.model_name`，但 LangChain 的 `ChatGoogleGenerativeAI` 没有 `provider` 属性，且 `model_name` 在 Gemini 上叫 `model`。

### 修复（6处patch）

```python
# browser_use/tokens/service.py
# line 347: f-string的llm.provider
provider = getattr(llm, 'provider', 'unknown')
logger.debug(f'LLM instance {instance_id} ({provider}_{llm.model}) ...')

# line 389: llm.provider == 'openrouter'
if getattr(llm, 'provider', None) == 'openrouter' or ...

# browser_use/agent/service.py
# line 1603: self.judge_llm.provider == 'browser-use'
if getattr(self.judge_llm, 'provider', None) == 'browser-use':

# line 2044: self.llm.provider in f-string
provider = getattr(self.llm, 'provider', 'unknown')
f'...provider={provider}...'

# line 2210: model_provider=self.llm.provider
model_provider=getattr(self.llm, 'provider', None),

# browser_use/agent/cloud_events.py
# line 217: agent.llm.model_name
llm_model=getattr(agent.llm, 'model_name', agent.llm.model),
```

## 根本兼容性问题（未解决）

### 1. Custom SystemMessage 不兼容

browser-use 0.12.8 使用自定义消息类型 `browser_use.llm.messages.SystemMessage`，但 Gemini 的 LangChain 集成只识别标准 `langchain_core.messages.SystemMessage`。

**错误**：`Unsupported message type: <class 'browser_use.llm.messages.SystemMessage'>`

### 2. output_format 透传不兼容

browser-use 将 `output_format=self.AgentOutput` 作为 kwarg 传给 `llm.ainvoke()`，这是为其自定义 `ChatBrowserUse` 类设计的。标准 LangChain 模型（包括 Gemini）使用 `llm.with_structured_output(schema)`。

### 3. session_id 透传不兼容

同 `output_format`，`session_id` 不是标准 LangChain ainvoke 的参数。

### 修复尝试

`agent/service.py` 中 get_model_output 方法：

```python
# 修复前（对Gemini报错"items" AttributeError）：
kwargs = {'output_format': self.AgentOutput, 'session_id': self.session_id}

# 修复后：
temperature = getattr(self.llm, 'temperature', 0.1) or 0.1
kwargs = {'temperature': temperature}
if hasattr(self.llm, 'provider') and self.llm.provider == 'browser-use':
    kwargs['output_format'] = self.AgentOutput
```

**效果**：导航（navigate）可以成功，但连续对话失败——第2步开始报SystemMessage不兼容。

## 结论

browser-use 0.12.8 假设 LLM 是 OpenAI/Anthropic 兼容的 API（标准 message types + 原生 function calling），与 Gemini via LangChain 存在根本性设计不匹配。

**推荐替代方案**：
1. **Playwright CDP 脚本**（已有 `~/.hermes/scripts/browser_cdp.py`）— Hermes自身做决策，脚本负责执行
2. **MCP Chrome Bridge**（`mcp-chrome-stdio`）— 但 bridge 进程经常崩溃需手动重启
3. **升级 browser-use 到 0.12.9+** — 可能有更好的模型兼容性
4. **使用 OpenAI/Anthropic API 驱动 browser-use**
