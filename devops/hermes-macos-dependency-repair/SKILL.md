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
# pyproject.toml: cryptography==50.0.1 → cryptography==48.0.1
# uv.lock: specifier = "==50.0.1" → specifier = "==48.0.1"
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
