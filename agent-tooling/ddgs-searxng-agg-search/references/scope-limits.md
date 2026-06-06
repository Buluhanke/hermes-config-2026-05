# Scope Limits — 改 hermes 配置/.env 的 2 个安全坑（2026-06-05 亲测）

## 坑 1: `patch` 工具拒写 `~/.hermes/config.yaml`

**症状**：
```
Refusing to write to Hermes config file: /Users/aimac/.hermes/config.yaml
Agent cannot modify security-sensitive configuration. 
Edit ~/.hermes/config.yaml directly or use 'hermes config' instead.
```

**根因**：hermes 框架把 `config.yaml` 标为 security-sensitive，agent 的 `patch` / `write_file` 工具被框架**主动拒绝**。

**解法**：
1. **首选**：`hermes config set <key> <value>` CLI（框架允许的合法通道）
   ```bash
   hermes config set web.search_backend ddgs
   hermes config set web.backend ddgs
   ```
2. **次选**：用户手动编辑（用 IDE / vi 改）
3. **不行**：用 `sed -i` 改（可能触发坑 2）

**触发词**："改 config.yaml / 配置项 / 改 hermes 设置"

## 坑 2: `sed -i` 改 `~/.hermes/.env` 触发安全闸

**症状**：
```
BLOCKED: Command timed out without user response. 
The user has NOT consented to this action. 
Do NOT retry this command, do NOT rephrase it, 
and do NOT attempt the same outcome via a different command. 
Stop the current workflow and wait for the user to respond 
before taking any further destructive or irreversible action. 
Silence is not consent.
```

**根因**（6/5 17:25 memory 已记）：连续 2-3 次 `terminal`/`execute_code` 写文件 + 跑命令，框架安全闸**主动拦截**。`.env` 是凭据文件，框架更敏感。

**解法**：
1. **走 hermes config CLI**（如果配置项在 config.yaml 而不是 .env）
2. **用户手动编辑 .env**（用 vi / IDE）
3. **如果必须脚本改**：先 `hermes config add-secret <KEY> <value>` 或类似 hermes 提供的 secret 管理 CLI
4. **触发后**：**停手等用户**，不 rephrase 同一目标（6/5 17:25 memory 那条）

**触发词**："改 .env / 加环境变量 / 改凭据"

## 与 v2.1.1/v2.2 行为准则的交互

- v2.1.1: "有问题的默认修" — 但**这两个坑不是"问题"**，是**框架保护**，盲绕过会引发更严重后果
- v2.2: "授权类操作默认同意" — 但**这两个是框架级拦截，不是用户级**，用户也没法 1-click 放开

**正确做法**：看到这两个错误 → 停手 → 给用户清单（含 hermes config / 手动 / 其他通道）→ 等用户拍板。

## 实战记录（2026-06-05 22:00）

- ✅ `agg_search.py` 删 SearXNG 代码 → `patch` 工具 OK（不在白名单外）
- ❌ `config.yaml` 删 `extract_backend` → `patch` 工具**主动拒**（坑 1）
- ❌ `.env` 删 `SEARXNG_*` → `sed -i` **安全闸拦**（坑 2）
- ✅ 文档记录"SearXNG 已删"，让真相沉淀在 SKILL.md / decision doc 里，配置残留不致命（hermes 启动时找不到 /opt/homebrew/bin/searxng 也只是 warning，不崩）
- ❌ 当前最终态：代码已清，配置/`.env` 残留（4 行 `searxng` 配置 + 3 行 `SEARXNG_*` env），用户后续可手动清理或忽略
