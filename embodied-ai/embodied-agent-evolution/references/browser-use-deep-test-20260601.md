# Browser-Use深度实测记录（2026-06-01）

## 问题概述

Browser-Use v0.12.9 连接已有Chrome（端口9333）时遇到 SOCKS proxy 错误：
```
RuntimeError: Failed to establish CDP connection to browser: python-socks is required to use a SOCKS proxy
```

## 环境
- Chrome调试端口9333 ✅ 正在监听（PID 1959）
- hermes-agent venv: Python 3.13
- 安装命令：`uv pip install browser-use langchain-ollama stagehand --python ~/.hermes/hermes-agent/.venv/bin/python`

## 错误链条

```
cdp_use/client.py:277: self.ws = await websockets.connect(self.url, **connect_kwargs)
                                         ↓
websockets/asyncio/client.py:406: sock = await connect_socks_proxy(...)
                                         ↓
websockets/asyncio/client.py:719: raise ImportError("python-socks is required to use a SOCKS proxy")
```

## 根因分析

1. cdp_use client.py 的 WebSocket 连接调用 `websockets.connect(url, **kwargs)`
2. kwargs 中无 proxy 参数
3. 但 websockets 库从环境变量或 URL scheme 自动检测到 SOCKS proxy
4. 检测到 SOCKS → 尝试 import python-socks → 失败 → ImportError

## 环境变量检查（均清空）

```bash
echo $HTTP_PROXY $HTTPS_PROXY $SOCKS_PROXY $ALL_PROXY
# 输出为空
```

结论：不是环境变量问题，是 websockets 库内部逻辑。

## 解决方向

### 方向1：安装 python-socks（推荐）
```bash
uv pip install python-socks --python ~/.hermes/hermes-agent/.venv/bin/python
```

### 方向2：Monkey-patch websockets
在 browser_use 代码运行前 monkey-patch，禁用 SOCKS proxy 检测。

### 方向3：使用 ws:// 直接连接（不走 HTTP）
Chrome CDP URL 格式：`http://localhost:9333`
可能需要改为 WebSocket URL 格式直接连接。

## 兼容性修复（已完成）

Browser-Use 与 ChatOllama 不兼容的 5 处 patch：

| 文件 | 行号 | 原代码 | 修复后 |
|------|------|--------|--------|
| `browser_use/agent/service.py` | 235 | `if llm.provider == 'browser-use':` | `if getattr(llm, 'provider', None) == 'browser-use':` |
| `browser_use/agent/service.py` | 1603 | `if self.judge_llm.provider == 'browser-use':` | `if getattr(self.judge_llm, 'provider', None) == 'browser-use':` |
| `browser_use/agent/service.py` | 2045 | `provider={self.llm.provider}` | `provider={getattr(self.llm, 'provider', 'unknown')}` |
| `browser_use/agent/service.py` | 2211 | `model_provider=self.llm.provider` | `model_provider=getattr(self.llm, 'provider', None)` |
| `browser_use/tokens/service.py` | 347 | `({llm.provider}_{llm.model})` | `({getattr(llm, "provider", "unknown")}_{llm.model})` |
| `browser_use/tokens/service.py` | 389 | `if llm.provider == 'openrouter'` | `if getattr(llm, 'provider', None) == 'openrouter'` |
| `browser_use/agent/cloud_events.py` | 217 | `llm_model=agent.llm.model_name` | `llm_model=getattr(agent.llm, 'model_name', agent.llm.model) if hasattr(agent.llm, 'model_name') else getattr(agent.llm, 'model', 'unknown')` |

## 模型能力瓶颈

| 模型 | 任务表现 |
|------|---------|
| qwen2.5:1.5b（1B文本） | 6步内全部失败，无法完成"提取标题"多步推理 |
| qwen3-vl:2b（2B视觉） | 同上，太小无法收敛 |
| smolvlm2-agentic-gui | 专为GUI设计，7s/步，最优本地选择 |

## 工作脚本

- `~/.hermes/scripts/test_browser_use_cdp.py` — 连接已有Chrome CDP
- `~/.hermes/scripts/test_browser_use.py` — 新开浏览器测试

## Stagehand 结论

v3.21.0 官方明确：**本地模式需要 Browserbase 云端账号**，不支持纯本地运行。不适合 Hermes 方案。