# Hermes 依赖版本验证方法论 — venv vs 系统 Python

## 背景问题（2026-06-02 BadHost CVE 实践教训）

当 BadHost CVE-2026-48710 (Starlette < 1.0.1) 披露时，方向 C 安全检查需确认
Hermes gateway 是否受影响。初始检查 `pip3 show starlette` 返回 Version: 1.0.0
(affected)，但这个版本来自**系统 Python 3.14 site-packages**。

## 正确做法

Hermes gateway 运行在自己的 venv 中，不依赖系统 Python 包。

```bash
# ❌ 错误：检查系统 Python
pip3 show starlette        # → 返回 1.0.0 (vulnerable) ← 但与 Hermes 无关！

# ✅ 正确：检查 Hermes venv
~/.hermes/hermes-agent/venv/bin/pip show starlette  # → 返回 1.0.1 (fixed!)
```

## 一键检查 all venv 依赖

```bash
# 列出 venv 中所有关键依赖版本
for pkg in httpx aiohttp requests pydantic uvicorn fastapi starlette; do
  ver=$($HOME/.hermes/hermes-agent/venv/bin/pip show $pkg 2>/dev/null | grep "^Version")
  echo "$pkg: $ver"
done

# 或遍历 dist-info 目录
ls ~/.hermes/hermes-agent/venv/lib/python*/site-packages/starlette-*.dist-info/ 2>/dev/null
```

## 系统 Python 版本何时有用

系统 Python 的 pip list 不用于 Hermes 运行时认定。仅在以下场景需要：
- 检查独立运行的 Python 工具（如 MCP 服务器）的依赖
- 检查 Ollama Python SDK（在系统 Python 而非 venv）

## Ollama 依赖栈的特殊性

Ollama (v0.24.0) 是 **Go 二进制** — 使用 Go 1.22+ net/http 标准库，
不包含任何 Python 包。因此搜索 "Ollama Starlette CVE" 方向有误。

Ollama 的依赖栈是 Go 生态（Go net/http, gin/chi 等），检查方向应为：
- Go 版本对应 HTTP 库 CVE
- Ollama 自身的绑定接口（`*:11434` all interfaces vs localhost-only）

## 实战验证结果（2026-06-02）

| 检查项 | 系统 Python | Hermes venv | Ollama |
|--------|-------------|-------------|--------|
| Starlette | 1.0.0 ❌ | **1.0.1 ✅** | N/A (Go) |
| FastAPI | - | 0.133.1 | N/A |
| httpx | - | 0.28.1 | N/A |
| aiohttp | - | 3.13.4 | N/A |
| 进程 | - | PID 90882 | PID 50269 |
| 绑定 | - | *:8642 | *:11434 |
