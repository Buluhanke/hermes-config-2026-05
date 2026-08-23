# 在 Hermes 网关环境下接入外部 Python / MCP 工具的 PYTHONPATH 污染坑

## 现象
在 Hermes（桌面网关）环境下用 `terminal` 跑外部 Python 工具或第三方 MCP server 时，进程会继承网关注入的环境变量：
```
PYTHONPATH=/Users/aimac/.hermes/hermes-agent:/Users/aimac/.hermes/hermes-agent/venv/lib/python3.11/site-packages
```
导致外部工具 import 时优先搜到 Hermes venv 的包，报以下错之一：
- `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`（fastmcp/pydantic 架构不匹配，3.14 vs 3.11）
- `ModuleNotFoundError: No module named 'mcp'`（venv 路径根本没被加进去，因为 venv 的 site-packages 解析也受 PYTHONPATH 干扰）

`env -i`（完全清空环境）也不行——venv 的 python 依赖 `pyvenv.cfg` 自动加 site-packages，但 Hermes 改过的 `sys.base_prefix` 或残留 PATH 会让它找不到自己的包。

## 解法（实测可用）
1. 给外部工具建**独立 venv**（用系统 `/usr/local/bin/python3`，不是 Hermes 的）：
   ```bash
   /usr/local/bin/python3 -m venv /tmp/tool/venv
   /tmp/tool/venv/bin/python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
2. 写 wrapper `run_clean.py`：
   ```python
   import sys, os
   os.environ.pop('PYTHONPATH', None)                       # 清掉 Hermes 注入
   venv_sp = '/tmp/tool/venv/lib/python3.14/site-packages'  # 用 venv 实际路径
   sys.path.insert(0, venv_sp)
   sys.path = [p for p in sys.path if 'hermes-agent/venv' not in p]  # 剔除 Hermes venv
   venv_py = '/tmp/tool/venv/bin/python'
   if sys.executable != venv_py:
       os.execv(venv_py, [venv_py, __file__])              # 用 venv 解释器重启自身
   import runpy
   runpy.run_path('/tmp/tool/server.py', run_name='__main__')
   ```
3. Hermes `mcp_servers` 里 command 指 `venv/bin/python`、args 指 wrapper：
   ```bash
   hermes config set mcp_servers.<name> '{"command":"/tmp/tool/venv/bin/python","args":["/tmp/tool/run_clean.py"],"enabled":true}'
   ```
   ⚠️ 工具守卫禁止手改 `~/.hermes/config.yaml`（会提示用 `hermes config`），改 MCP 用 `hermes config set mcp_servers.<name> '<json>'`。
4. 重启网关加载（`kill -9` 旧网关 PID，KeepAlive 自动拉起新实例）。

## 验证是否加载
- 进程存活：`pgrep -f run_clean.py`
- 不要用 `printf '...' | venv/bin/python server.py` 测 stdio 握手——pipe 模式会卡 180s 超时，是测试方式问题不是 MCP 问题。直接看 Hermes 是否拉起进程即可，或等用户回来后用 Hermes 内部 MCP 调用验证返回值。

## 实测案例
1688-Scraper-MCP（github: xiayumu034-crypto/1688-Scraper-MCP，用 DrissionPage 驱动真实 Chromium）。用此 wrapper 后 Hermes 正常拉起进程（pid 93792/93796 存活），import 冲突消失。代码审查安全（无外部数据外传、登录态存本地 `drission_user_data`），但 `search_1688_products` 实际返回**未验证**（用户中途离开）。
