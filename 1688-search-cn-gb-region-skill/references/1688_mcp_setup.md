# 1688-Scraper-MCP 接入 Hermes 实录（2026-08-20）

仓库：`xiayumu034-crypto/1688-Scraper-MCP`（GitHub）。基于 DrissionPage 驱动真实 Chromium，
工具：`search_1688_products(keyword, page_num, location_filter, only_factory, max_results)` /
`get_product_detail_and_price(url)` / `get_product_reviews(url)` / `analyze_supplier_reliability(url)` /
`update_auth_cookie(url)`。

## 安全评估（已做）
- 仅本地 Chromium 读 1688 公开页，无外传请求，无未知域名
- 登录态存本地 `drission_user_data/` 目录，不离开本机
- 依赖均为正常 PyPI 包（fastmcp / drissionpage / requests 等）

## 安装坑（必踩，已解决）

### 坑1：Hermes 网关注入 PYTHONPATH 污染外部 venv
Hermes gateway 启动时给所有子进程注入 `PYTHONPATH=/Users/aimac/.hermes/hermes-agent/venv/lib/python3.11/site-packages`。
外部 venv 的 python 会优先搜到 Hermes venv 的 pydantic → 崩：
`ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`

**修法**：建隔离 venv + `bootstrap.py` 在 server.py 前清环境：
```python
# bootstrap.py
import os, sys
os.environ.pop('PYTHONPATH', None)
VENV_SP = '/Users/aimac/.hermes/1688-mcp/venv/lib/python3.14/site-packages'
sys.path.insert(0, VENV_SP)
sys.path = [p for p in sys.path if 'hermes-agent/venv' not in p and p not in ('', '.')]
import runpy
sys.argv = ['server.py']
runpy.run_path('/Users/aimac/.hermes/1688-mcp/repo/server.py', run_name='__main__')
```

### 坑2：/tmp 会被系统清理
早期放 `/tmp/1688mcp`，用户离开期间 venv 被清，MCP 重启报 `No such file or directory`。
**一律放持久位置**：`~/.hermes/1688-mcp/{repo,venv}`。

### 坑3：PermissionError on run.sh
Hermes mcp watchdog 用受限方式 exec，`.sh` 的可执行位不一定够。
**直接用 venv python 绝对路径 + bootstrap.py 作 args**，command 不要指向 .sh。

## 安装步骤
```bash
# 1. 克隆到持久位置
mkdir -p ~/.hermes/1688-mcp && rm -rf ~/.hermes/1688-mcp/repo
git clone --depth 1 https://github.com/xiayumu034-crypto/1688-Scraper-MCP.git ~/.hermes/1688-mcp/repo

# 2. 隔离 venv（用系统 /usr/local/bin/python3，3.14）
/usr/local/bin/python3 -m venv ~/.hermes/1688-mcp/venv
~/.hermes/1688-mcp/venv/bin/python -m pip install -r ~/.hermes/1688-mcp/repo/requirements.txt \
  -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 写 bootstrap.py（内容见上）
# 4. 加进 Hermes config（用 hermes config set，勿手改 config.yaml——工具守护会拦）
hermes config set mcp_servers.alibaba_1688_scraper \
  '{"command":"/Users/aimac/.hermes/1688-mcp/venv/bin/python","args":["/Users/aimac/.hermes/1688-mcp/repo/bootstrap.py"],"enabled":true}'

# 5. 重启网关（kill -9 旧 gateway PID，LaunchAgent KeepAlive 自动拉起新实例）
# 注意：禁止在 gateway 进程内自重启；用 kill -9 触发自动重启
```

## 验证握手（不走 printf|python pipe，会超时——那是测试方式问题不是 MCP 问题）
用文件传 JSON 到 stdin：
```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' > /tmp/mcp_init.json
~/.hermes/1688-mcp/venv/bin/python ~/.hermes/1688-mcp/repo/bootstrap.py < /tmp/mcp_init.json
# 期望返回 serverInfo: 1688_Scraper_MCP
```

## 当前状态（2026-08-20 最终定论）
- ✅ 握手成功、工具可调用
- ✅ **登录态已成功持久化**（`drission_user_data/` 已登录 1688；`www.1688.com` 首页 `has_user=True`、`detail.1688.com` 直开商品页无墙）。登录脚本已收编进 skill：`scripts/login_1688.py`（走 `member.1688.com` 主站入口，留 180s 扫码窗口）。
- ❌ **`search_1688_products` 端点级风控**：`s.1688.com/selloffer/offer_search.htm` 对自动化浏览器强制踢回 `login.taobao.com` 中转页，**即便已登录也照样踢**（已用 `scripts/verify_endpoints.py` 复现：先过首页 session 再跳搜索页仍 BLOCKED）。这是端点风控，非 cookie 域问题。
- ⚠️ **MCP 现状 = 半自治**：搜索仍走方案0（真 Chrome + AppleScript 抓 ID）；拿到 ID 后用 MCP `get_product_detail_and_price`（走 `detail.1688.com`，已登录免墙）拿结构化价格，比方案0 逐个开详情页更稳更快。
- 裸 repo（`~/.hermes/1688-mcp/repo/`）现仅留 `server.py` + `bootstrap.py` + `drission_user_data/`；登录/验证脚本统一在 skill `scripts/` 下，勿在裸 repo 另存副本（避免两处漂移）。

## 注意
- `search_1688_products` 默认 URL 只传 `keywords`+`beginPage`，**不带 province 参数**，且端点被风控不可用。要搜江浙沪请用方案0（`scripts/run_search.scpt`）。
- 若要让 MCP 搜索也通：需改 `server.py` 的 `search_1688_products` 搜索 URL 换成不被风控的端点（待探索）。
- 登录态过期/清缓存后：跑 `scripts/login_1688.py` 重新扫码（详见 SKILL.md「重登录流程」）。
- 改 server.py 后需重启网关重载 MCP。
