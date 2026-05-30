# browser-use — Local Browser Automation for AI Agents

## Overview
GitHub: https://github.com/browser-use/browser-use (91K Stars)
License: MIT, open source
**Status (2026-06-01实测)**: 框架已完全修复可用，连接已有Chrome CDP需python-socks，本地VLM推理能力仍不足

---

## 完整安装与配置（2026-06-01实测）

### 依赖路径（重要！）
- **Hermes Agent venv**: `~/.hermes/hermes-agent/.venv` (Python 3.13)
- **Browser-Use 安装**: 必须装到 Hermes Agent venv，不是系统Python
- **Chrome 调试端口**: `localhost:9333` (手动启动的 chrome-debug profile)

### 安装步骤

```bash
# 1. 安装到正确venv
cd ~/.hermes/hermes-agent && source .venv/bin/activate
uv pip install browser-use langchain-ollama

# 2. 安装python-socks（CDP WebSocket连接需要）
uv pip install python-socks --python ~/.hermes/hermes-agent/.venv/bin/python

# 3. 启动Chrome带调试端口（如果还没运行）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/.hermes/chrome-debug" &
```

### 兼容性修复（必须做，5处patch）

Browser-Use 0.12.9 检查 `llm.provider` 和 `llm.model_name`，但 ChatOllama 没有这些属性。需要patch 5处：

| 文件 | 原代码 | 修复 |
|------|--------|------|
| agent/service.py:235 | `if self.judge_llm.provider == 'browser-use':` | `if getattr(self.judge_llm, 'provider', None) == 'browser-use':` |
| agent/service.py:1603 | `provider={self.llm.provider}` | `provider={getattr(self.llm, 'provider', 'unknown')}` |
| agent/service.py:2045 | `model_provider=self.llm.provider` | `model_provider=getattr(self.llm, 'provider', None)` |
| agent/service.py:2211 | `llm_model=agent.llm.model_name` | `llm_model=getattr(agent.llm, 'model_name', agent.llm.model) if hasattr(...) else ...` |
| tokens/service.py:347,389 | `self.llm.provider` | `getattr(self.llm, 'provider', None)` |

**自动化patch脚本**（保存到 `scripts/patch_browser_use.sh`）：
```bash
#!/bin/bash
BASE="$HOME/.hermes/hermes-agent/.venv/lib/python3.13/site-packages/browser_use"

sed -i "s/if self\.judge_llm\.provider == 'browser-use':/if getattr(self.judge_llm, 'provider', None) == 'browser-use':/g" $BASE/agent/service.py
sed -i "s/provider={self\.llm\.provider}/provider={getattr(self.llm, 'provider', 'unknown')}/g" $BASE/agent/service.py
# ... 完整脚本
```

### 使用示例

```python
import asyncio, os
for k in ['HTTP_PROXY','HTTPS_PROXY','SOCKS_PROXY','ALL_PROXY']:
    os.environ[k] = ''  # 清除代理，否则websockets报SOCKS错误

from browser_use import Agent
from langchain_ollama import ChatOllama
from browser_use.browser.profile import BrowserProfile

async def test():
    profile = BrowserProfile(cdp_url='http://localhost:9333', is_local=True)
    llm = ChatOllama(model='qwen3-vl:latest', keep_alive=300, temperature=0.0)
    
    agent = Agent(
        task='Navigate to httpbin.org/html and extract the page title',
        llm=llm,
        browser_profile=profile,
        max_steps=8,
    )
    result = await agent.run()
    print(result.final_result)

asyncio.run(test())
```

### CDP连接已有Chrome的正确方式

1. **启动Chrome带调试端口**（只需做一次，以后Chrome常驻9333）：
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/.hermes/chrome-debug" &
```

2. **确认端口监听**：
```bash
lsof -i :9333  # 看到 Google Chrome LISTEN 即成功
```

3. **传入正确cdp_url**：
```python
profile = BrowserProfile(cdp_url='http://localhost:9333', is_local=True)
# 注意是 http:// 不是 ws://
```

### 模型能力测试结果（2026-06-01）

| 模型 | 导航 | 内容提取 | 结论 |
|------|------|----------|------|
| qwen2.5:1.5b | ✅ | ❌ | 太小，推理循环不收敛 |
| qwen3-vl:2b | ✅ | ❌ | 同上 |
| qwen3-vl:latest (6.1GB) | ✅ | ❌ | 仍不够，6步内全部失败 |

**结论**: Browser-Use 框架完全正常，瓶颈在本地VLM推理能力。需要更大参数模型（qwen3-vl:14b+）或云端GPT-4o。

---

## 核心坑（SOCKS Proxy — 2026-06-01解决）

### 问题现象
```
ERROR: Failed to establish CDP connection to browser: python-socks is required to use a SOCKS proxy
```

### 根因
`websockets` 库检测到系统级 SOCKS 代理设置，自动走 SOCKS 协议，但没装 `python-socks` 导致 ImportError。清空环境变量 `HTTP_PROXY` 等无效（因为是 SOCKS 不是 HTTP proxy）。

### 解法
```bash
uv pip install python-socks --python ~/.hermes/hermes-agent/.venv/bin/python
```

装完立即生效，不需要改代码。

---

## 已知限制

1. **1688反爬**: 和Playwright一样被检测，返回虚假HTML。换Selenium或换平台。
2. **本地VLM推理弱**: 即使qwen3-vl:7b，内容提取仍失败。需要更大参数模型。
3. **页面ready timeout**: httpbin.org/html 等简单页面3s timeout可能不够，用 `max_steps` 控制重试。
4. **Stagehand官方需付费**: 官网明确本地模式需额外配置MCP server，不是开箱即用

---

## 相关工具

- **Playwright** (Microsoft): 更底层浏览器控制，需要更多代码
- **Stagehand**: 官方云端收费，本地MCP方案需额外配置
- **cdp_use**: 直接Python WebSocket + CDP，控制更底层