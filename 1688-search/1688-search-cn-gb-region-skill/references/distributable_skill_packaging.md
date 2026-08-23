# 把 Hermes skill 做成可分发包（通用做法，2026-08-20 实战验证）

场景：一个 skill 在本地调通后，要 `cp -R` / 解压 tar 到**另一台机器 / 另一个 Hermes 实例**直接能用。
1688 找品 skill 是第一个这么做的，本文件抽成通用 recipe，任何带 Python 依赖 / MCP / 外部进程的工具型 skill 都照此改造。

## 判定：当前 skill 能不能直接分发？
跑一遍自检，有一条命中就不能直接分发：
1. 脚本里写死 `/Users/xxx` / `/home/xxx` 等绝对路径 → 换机器全断
2. 依赖放在 skill 目录**之外**（裸 repo / 系统某处 venv / `/tmp`）→ 对方没有
3. 依赖 Hermes 全局 `config.yaml` 里的 `mcp_servers.<name>`（不随 skill 走）
4. 把**登录态 / 账号 cookie / 凭证目录**打进了包 → 绑定原账号设备，污染对方

## 改造步骤（照做）

### 1. MCP / 外部工具本体收进 skill
建 `mcp/`（或 `bin/`）子目录，把 `server.py`/`bootstrap.py`/`requirements.txt` 放进去。
不再依赖外部裸 repo。skill 成为自包含单元。

### 2. 路径全相对化（最关键）
- Python：所有"skill 根目录"从 `__file__` 推断，绝不在源码写死机器路径：
  ```python
  HERE = os.path.dirname(os.path.abspath(__file__))      # .../skill/scripts 或 .../skill/mcp
  SKILL_ROOT = os.path.dirname(HERE)                     # .../skill
  VENV_SP = os.path.join(SKILL_ROOT, 'venv', 'lib', 'python3.14', 'site-packages')
  USER_DATA = os.path.join(SKILL_ROOT, 'venv', 'drission_user_data')
  ```
  改完验证：`exec` 整段常量时把 `__file__` 设成假路径（如 `/home/someone/.hermes/skills/X/scripts/y.py`），确认 `USER_DATA` 跟着变、不含原机路径。
- AppleScript（`*.scpt`）：用 `POSIX path of (path to me)` 拿到自身路径，`dirname` 推出 scripts 目录：
  ```applescript
  set myPosix to POSIX path of (path to me)
  set scriptDir to do shell script "dirname " & quoted form of myPosix
  set jsRead to read (POSIX file (scriptDir & "/check_spec.js")) as «class utf8»
  ```
- 输出文件可写 `/tmp/xxx.txt`（每台机都有，不绑机器）；不要写 skill 内相对路径除非有把握。

### 3. 隔离 venv 随 skill 走
- venv 建在 `<skill根>/venv/`（用系统 `python3 -m venv`，不是 Hermes 的 venv）。
- `bootstrap.py`（MCP 启动包装）在加载 server 前清掉 Hermes 网关注入的 `PYTHONPATH`，强制用 venv 的 site-packages：
  ```python
  os.environ.pop('PYTHONPATH', None)
  VENV_SP = os.path.join(SKILL_ROOT,'venv','lib','python3.14','site-packages')
  if os.path.isdir(VENV_SP): sys.path.insert(0, VENV_SP)
  sys.path = [p for p in sys.path if 'hermes-agent/venv' not in p and p not in ('','.')]
  import runpy; sys.argv=['server.py']; runpy.run_path(SERVER, run_name='__main__')
  ```
- 国内装包走清华镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`，失败回退官方。

### 4. 写 setup.sh（接收方一键）
做三件事并打印后续命令：
```bash
bash setup.sh
# 内部：/usr/bin/python3 -m venv venv；venv/bin/python -m pip install -r mcp/requirements.txt
# 打印：hermes config set mcp_servers.<name> '{"command":"<绝对路径>/venv/bin/python","args":["<绝对路径>/mcp/bootstrap.py"],"enabled":true}'
# 提示：对方自己跑 login 脚本扫码登录
```
注意：MCP 运行时 `command` 必须指向 `venv/bin/python` + `bootstrap.py`，**不要**指向 `.sh`（Hermes watchdog 对 .sh 可执行位受限）。setup.sh 仅用于首次安装。

### 5. 登录态 / 凭证绝不随包走
- `drission_user_data/`、`*.login_state.json` 这类**含账号登录态**的目录，绑定原账号+设备，打包前 `rm -rf`。
- 硬塞进包 = 对方加载的是你的会话，不仅污染还可能触发风控。
- 对方必须自己跑登录脚本扫码。SKILL.md 明确写"登录态不随包走，接收方本人扫码"。

### 6. 收尾校验
```bash
grep -rn "/Users/aimac" .        # 应零残留（历史说明文字可保留，但不得是路径依赖）
bash -n setup.sh                 # 语法 OK
# 换假 __file__ exec 验证 USER_DATA 推断正确（见步骤 2）
```
最后 `tar czf skill.tar.gz skill/` 交给对方。

## 能力边界要写清（避免对方误用）
分发包必须在 README / SKILL.md 顶部写清：哪些通道可用、哪些端点被风控、登录怎么处理。
例：1688 的 `search_1688_products` 端点级风控（自动化浏览器必被踢回 login.taobao.com），所以搜索只能走方案0，MCP 只拿详情页价格——对方不知道会白等。

## 反模式（勿做）
- 不要把 `/tmp` 当持久位置（系统会清，MCP 重启即丢）。
- 不要手改接收方的 `~/.hermes/config.yaml` 加 MCP（工具守护会拦），用 `hermes config set`。
- 不要把整套 skill 写成"只给我这台机器用的脚本合集"——每次换机器都重写是浪费。
