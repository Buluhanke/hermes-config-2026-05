---
name: hermes-macos-dependency-repair
description: "Use when hermes uv sync fails on macOS."
version: 1.0.0
author: hermes-agent
license: MIT
metadata:
  hermes:
    tags: [hermes, macos, dependency, repair, uv]
    related_skills: [hermes-model-health]
---

## When to Use
- `hermes` 报 `no dependency environment is committed for this install`
- `uv sync` 编译 Rust 包失败：`Could not find openssl via pkg-config`
- Hermes 启动后报 `automatic dependency repair retry limit reached`
- venv 路径不匹配 runtime facts（`venv` vs `.venv`）

## 诊断步骤

1. **确认 Python 版本**：`hermes --version`
2. **检查 venv**：`ls .venv/bin/python && .venv/bin/python -c 'import openai'`
3. **检查 runtime facts**：`pm.environments.selected_venv(root)` 是否指向存在的目录
4. **检查 .repair-incomplete 标记**：`ls <install_state_dir>/.repair-incomplete`

## 修复流程

### 步骤 1：解决 OpenSSL/pkg-config 缺失

macOS（尤其 Intel/黑苹果）常无 Homebrew。两种方案：

**方案 A — 编译 OpenSSL 源码**：
```bash
cd /tmp/openssl-3.2.2
make -j4 && make install  # 安装到 ~/.local/opt/openssl@3
export OPENSSL_DIR=~/.local/opt/openssl@3
export PKG_CONFIG_PATH=~/.local/opt/openssl@3/lib/pkgconfig
```

**方案 B — 用预编译 wheel**（更快）：
```bash
python3 -m pip download cryptography --only-binary :all: --no-deps -d /tmp/cryptowheels
.venv/bin/python -m pip install /tmp/cryptowheels/cryptography-*.whl
```

### 步骤 2：更新版本锁定

修改 `pyproject.toml` 和 `uv.lock` 中的版本号（两者都要改）：
```bash
# pyproject.toml: cryptography==<锁定版本> → <目标平台有 wheel 的版本>
# uv.lock: specifier = "==<锁定版本>" → specifier = "==<新版本>"
```

### 步骤 3：重建 venv

```bash
cd ~/.hermes/hermes-agent
rm -rf .venv venv
python3.14 -m venv .venv
.venv/bin/pip install -e .
ln -s .venv venv  # runtime facts 期望 venv 目录
```

### 步骤 4：清除修复循环标记

```bash
rm -f <install_state_dir>/.repair-incomplete
rm -f <install_state_dir>/source-completion-pending
```

### 步骤 5：验证

```bash
.venv/bin/python -m hermes_cli.main --version
.venv/bin/python -m hermes_cli.main gateway status
```

## Pitfalls

1. **uv.lock 也要改**：只改 pyproject.toml 不够，uv sync 仍按 uv.lock 旧版本编译。
2. **venv vs .venv 路径**：runtime facts 记录的路径必须存在。facts 指向 `venv` 但实际是 `.venv` 时，创建 symlink。
3. **.repair-incomplete 循环**：该标记存在时 hermes 每次启动都尝试自动修复，失败后计数+1，达到上限报 `retry limit reached`。修好后必须删除。
4. **source-completion-pending**：存在时也会触发修复。修好后删除。
5. **PYTHONPATH 污染**：运行外部命令前用 `env -i` 清环境。
6. **预编译 wheel 版本**：pip 安装的 wheel 版本可能低于 pyproject.toml 锁定版本。同步更新锁文件，否则 uv sync 会覆盖。
7. **跨机迁移别走重建路线**：如果报错来自另一台 Mac 拷来的 `~/.hermes`（CLI 卡死、`no dependency environment is committed`、`sample` 显示停在 `_dyld_start`），先清 `com.apple.quarantine`、改硬编码路径，再直接拷贝已构建的 venv 到目标机自己的 install-state 目录并重写 stamp；完整流程和判定依据见 `hermes-local-capabilities-macos` 技能里的 cross-machine-hermes-clone 参考文档。目标机拉不到包索引时 `hermes pm repair` / `uv sync` 会一直挂着，靠等修不好。

8. **arm64→Intel 跨架构克隆（不能复用 venv）**：先 `uname -m` 确认。arm64 venv 的 `.so` 在 Intel 上是 `bad CPU type`，必须重建。两条前置判据（SSL 证书、目标平台 wheel 可用性）见下面第 9、10 条；踩坑链：
   - **依赖树可能整体绑死解释器**：若 `uv.lock` 把所有包标成 `python_full_version >= '3.14'`，降到 3.12 只会装上零个包，并在旧包元数据构建时报 `cannot import name 'msvccompiler' from 'distutils'` 之类的旁支错误。先读 `requires-python` 和 marker 再选解释器。
   - **不要删 facts.json 的 stamp**：删了会让 pm 判定 venv 失效→后台 `uv lock`+`pm/worker.py` 死循环持有 `.install.lock`，对话进程一直等锁。正确做法是用 `pm.install.get_package('venv').expected_stamp(enabled, **_member_inputs(None))` 重算；注意 `pm.paths.facts_path()` 可能指向 `~/.hermes/tools/facts.json`（空文件），**要写的是 `runtime_facts_path()`**（install hash 目录下），extras 从该 facts.json 直接读。写完后 `venv_is_current()` 必须为 True。
   - **解释器版本必须和 venv 一致**：启动脚本 `.hermes/bin/hermes` 第一行 `exec <python>` 若指向 3.14 而 venv site-packages 是 cp312，gateway 会报 `cannot import name 'ArgsKwargs' from pydantic_core`。把第一行改成 `<install-dir>/environments/<env>/venv/bin/python`（即 venv 自己的解释器）。判断法：`venv/bin/python -V` 和 site-packages 目录名 `python3.x` 必须一致。
   - **手动装依赖会漏包**：`uv export --format requirements.txt` + 去掉 marker/hash/Windows 包（winrt、pywin32）后 pip `--no-deps` 装能装齐大部分，但 **aiohttp 依赖链**（aiohttp+propcache+multidict<7+yarl+frozenlist+aiohappyeyeballs+attrs）容易漏，缺了 gateway 报 `AttributeError: 'NoneType' object has no attribute 'Response'`（web 为 None）。用 `pip install 'aiohttp>=3.11,<3.13'` 让 pip 自动解析装齐。
   - **gateway 重启**：`pkill -f gateway` / `launchctl kickstart` 会被守卫拦（禁止从 gateway 内杀 gateway），用官方 `hermes gateway restart`。drain 有等待期，日志 `Shutdown phase` 结束后才是新进程。
   - **最后一步 provider**：若 config `provider: nous` 但无 Nous access token，对话返回 `No access token found for Nous Portal login`。有 OPENROUTER_API_KEY 就把 config.yaml 的 `provider: nous`→`openrouter`、`default:` 改成有效免费模型（如 `nvidia/nemotron-3.5-lightning:free`），注释掉 nous base_url，重启 gateway 即可端到端跑通。
   - **找"原来的独立 bot"必查 preclone 备份**：用户说"恢复原来配置的 bot/渠道"时，先 `find /Users -maxdepth 3 -type d -iname '*bak*preclone*'`——clone 前备份目录（如 `~/.hermes.bak-preclone-YYYYMMDD`）里藏着目标机**真正的独立 token**。本例当前 `~/.hermes/.env` 全是 clone 带来的 Mac mini token（重叠），而 preclone 备份里有独立的 `TELEGRAM_BOT_TOKEN`（本机专属 bot）。用 `curl https://api.telegram.org/bot<token>/getMe` 验证归属（返回的 first_name/username 能确认是哪台机器的 bot）。**不要只看当前 env 就断言"没有独立渠道"**。
   - **恢复独立 bot 的正确姿势**：①注释掉当前 env 里 clone 带来的重叠 token（保留原值可逆）②把 preclone 的独立 token 追加进当前 env ③park 掉含重叠 token 的 secondary profile（`touch ~/.hermes/profiles/<name>/gateway.parked`）④`config.yaml` 设 `gateway.multiplex_profiles: false` 只跑 default ⑤`gateway install && gateway start`。
   - **gateway 停了又被 launchd 拉起**：`hermes gateway stop` 挡不住 launchd 的 RunAtLoad/KeepAlive（进程秒回）。要真正停必须 `hermes gateway uninstall`（删 plist + bootout）。`launchctl bootout` 会被守卫拦（判定在 gateway 进程树内），用官方 uninstall。
   - **gateway install 会把启动脚本 python 改回 3.14**：重装服务后检查 `.hermes/bin/hermes` 第一行，若是 3.14 而 venv 是 cp312，改回 `<venv>/bin/python`（否则 pydantic_core `ArgsKwargs` 导入失败）。改完要 `gateway restart`。
   - **Telegram adapter 缺依赖**：日志 `Platform 'Telegram' requirements not met` + `No adapter available for telegram`，是缺 `python-telegram-bot[webhooks]==22.8`（pyproject telegram extra）。手动 pip 装齐。成功标志：gateway.log 出现 `✓ telegram connected` / `Connected to Telegram (polling mode)`。此路只适用于同架构；跨架构见参考文档。
9. **python.org Python 的 SSL 证书**：pip/urllib 报 `UNEXPECTED_EOF_WHILE_READING` / `CERTIFICATE_VERIFY_FAILED` 而 `curl` 正常时，是 python.org 解释器没配 framework 证书，不是网络问题；给 `pip` / `uv` / `hermes pm` 命令加 `SSL_CERT_FILE=/etc/ssl/cert.pem`（需要时再加 `REQUESTS_CA_BUNDLE=/etc/ssl/cert.pem`），别去改代理或关证书校验。构建 sdist 时 pip 会在隔离环境里重跑自身，外层命令设的变量传不进去，必须同时设 `PIP_CERT=/etc/ssl/cert.pem`，否则 build dependencies 阶段照样 SSL 失败。
10. **编译 cryptography 前先查 wheel**：若 uv sync 卡在编译 cryptography，先用 `pip download --only-binary :all: --no-deps cryptography==<版本>` 或 PyPI JSON 确认目标平台有 wheel；部分新版本在 macOS 只发 arm64 wheel，Intel 必须编译，而编译需要 OpenSSL 头文件和 pkg-config，先备齐再动手。
