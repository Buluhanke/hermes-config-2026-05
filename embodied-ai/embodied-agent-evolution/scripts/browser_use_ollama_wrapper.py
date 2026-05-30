#!/usr/bin/env python3
"""
Browser-Use + Ollama 本地VLM wrapper
解决 ChatOllama 与 Browser-Use 不兼容问题（pydantic model 不能动态添加属性）

使用方法：
1. 直接 import 这个 wrapper
2. 用 OllamaWrapper(llm_base) 包装 ChatOllama
3. 把包装后的 llm 传给 Agent

示例：
```python
from browser_use import Agent
from langchain_ollama import ChatOllama
from hermes_scripts.browser_cdp import OllamaWrapper  # 或直接用这个文件

llm_base = ChatOllama(model='qwen3-vl:2b', base_url='http://localhost:11434/v1', temperature=0.1)
llm = OllamaWrapper(llm_base)

agent = Agent(llm=llm, task='打开 example.com，告诉我页面标题')
asyncio.run(agent.run())
```

注意：
- browser-use 装在 Python 3.14 环境（/usr/local/bin/python3.14）
- 需要先 patch browser_use/agent/service.py 第235行：
  if getattr(llm, 'provider', None) == 'browser-use':
"""
import asyncio
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel


class OllamaWrapper(BaseChatModel):
    """Wrapper that adds provider/model_name to ChatOllama for Browser-Use compatibility.
    
    Browser-Use checks llm.provider == 'browser-use' and llm.model_name.
    ChatOllama (pydantic model) doesn't expose these attributes natively.
    This wrapper adds them as properties without violating pydantic constraints.
    """
    _llm: ChatOllama
    
    def __init__(self, llm: ChatOllama, **kwargs):
        super().__init__(**kwargs)
        self._llm = llm
        self._provider = 'ollama'
        self._model = llm.model
    
    @property
    def provider(self):
        return self._provider
    
    @property
    def model(self):
        return self._model
    
    @property
    def model_name(self):
        return self._model
    
    def _llm_type(self) -> str:
        return "ollama"
    
    def _generate(self, **kwargs):
        return self._llm._generate(**kwargs)
    
    def _call(self, messages, **kwargs):
        return self._llm._call(messages, **kwargs)


if __name__ == '__main__':
    # Test with example.com
    llm_base = ChatOllama(
        model='qwen3-vl:2b',
        base_url='http://localhost:11434/v1',
        temperature=0.1
    )
    llm = OllamaWrapper(llm_base)
    
    from browser_use import Agent
    
    agent = Agent(
        llm=llm,
        task='打开 example.com，告诉我页面标题是什么'
    )
    
    print('🚀 Running Browser-Use with local Ollama...')
    result = asyncio.run(agent.run())
    print('Result:', result)