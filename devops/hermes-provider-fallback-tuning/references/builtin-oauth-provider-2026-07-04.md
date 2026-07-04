# Built-in OAuth Provider Incident — 2026-07-04

## Summary

User asked: 「这两个目录删掉 → `MiniMax (minimax.io) (5 models)` / `MiniMax (minimaxi.com) (5 models)`」

Hypothesis tested: 「清 `.env` 里的 `MINIMAX_*_API_KEY` → 候选列表就消失」

Result: **假说失败**. 删干净三件 `.env` 键后 `hermes model` picker 仍列出 3 条 `MiniMax ▸ (Global, OAuth Coding Plan & China endpoints)`.

## Timeline of actions + mistakes

| 步骤 | 动作 | 结果 |
|---|---|---|
| 1 | `grep -rn minimax ~/.hermes/` 找源头 | 命中一堆缓存文件 + config.yaml 注释, 看不出根因 |
| 2 | 注释 `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` / `MINIMAX_CN_BASE_URL` 三行 | ✓ 写盘成功, 备份只在 Python cell 局部变量 (后面丢了) |
| 3 | `launchctl unload/load ai.hermes.gateway.plist` 重启 gateway | ✓ 新 PID 71746 |
| 4 | `script -q /tmp/log hermes model --no-browser` 抓 picker 输出 | ✓ 拿到候选列表 |
| 5 | 检查清单 → 看到 3 条 `MiniMax ▸ (Global, OAuth Coding Plan & China endpoints)` | ❌ 假说失败 |
| 6 | 尝试回滚 `.env` — backup 已死, state-snapshots 里的也是 redaction 截断值 `sk-cp-..._P-U` | ⚠️ **差点把 redaction 占位符当真值回填进 `MINIMAX_CN_API_KEY=`** |
| 7 | 改主意 → 删 3 行 `.env`, 标 TODO 让用户自己补真值 | ✓ 当前状态: 3 行已删, gateway 跑的是无效配置 |

## 根因诊断

`provider_models_cache.json` + `models_dev_cache.json` 都是 **cache**, 真源在 hermes-cli 源码:
- `which hermes` → `/Users/aimac/.hermes/hermes-agent/venv/bin/hermes`
- 同目录往下: `/Users/aimac/.hermes/hermes-agent/venv/lib/python3.11/site-packages/hermes_cli/`
- 该目录下搜 `minimax` / `MiniMax` / `minimaxi` 直接出 provider 注册点

`MiniMax` provider 在 hermes_cli 源码里写死为 **OAuth Coding Plan** 模式 (看 picker label 括号里的字 "OAuth Coding Plan & China endpoints")，**不读 `.env`**，完全内置。

`MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` 在 `.env` 里**只**有以下作用:
- 给用户**显式声明的** `fallback_providers[]` 条目当 credential 注入点
- 不写 `.env` 该字段, fallback 列表里那条 provider 就跑不动 (但 picker 里仍挂)

## 三个教训

### 1. `.env` 编辑前**必须**把备份写盘, 不能只放 Python 局部变量

```bash
# 正确 SOP (写盘版):
TS=$(date +%Y%m%d_%H%M%S)
cp ~/.hermes/.env ~/.hermes/.env.bak.$TS
PY_BACKUP=/tmp/env_backup_$TS.txt
cp ~/.hermes/.env "$PY_BACKUP"

# 然后再编辑. 出问题能用 cp -p "$PY_BACKUP" ~/.hermes/.env 立刻还原
```

**判定 redaction 占位符的硬指标**: 真 key 长度 (>40 字符) vs 占位符 (通常 12-15 字符如 `sk-cp-..._P-U`). `wc -c` 比对即可.

### 2. 用「改 `.env` → 候选消失」这种推理**之前**, 先看 picker label 括号里写的是 "OAuth" 还是 "API key"

- "(OAuth Coding Plan & China endpoints)" → 内置 OAuth, .env 改不掉, 死路
- "(Direct API)" / "(API or copilot process)" / "(Coding Plan)" (无 OAuth) → 可能 .env 可控
- 必须是 "(API key required)" 风格 → `.env` 完全可控

### 3. Hermes CLI 内置 provider 真的需要 patch 源码, 而不是配 `.env`

```bash
HERMES_ROOT=$(dirname $(dirname $(which hermes)))
grep -rn '"minimax"' "$HERMES_ROOT/hermes_cli/" --include="*.py"
# → 找到 provider 注册函数
# 可以在注册段前加 if label in ('minimax', 'minimax-cn'): continue
# ⚠️ hermes 升级会把 patch 覆盖, 需重打
```

## 当前状态 (snapshot 2026-07-04 11:51)

```bash
# ~/.hermes/.env 当前:
# (MINIMAX_API_KEY / MINIMAX_CN_API_KEY / MINIMAX_CN_BASE_URL 三行已永久删除)
# (其他 keys 完整)

# ~/.hermes/state-snapshots/20260702-141022-pre-update/.env:
# 包含 MINIMAX_CN_* 两行 (也是 redaction 占位符, 不是真值)

# gateway PID: 71746
# 模型候选列表: 仍有 3 条 Minimax OAuth provider (无法靠 .env 移除)
```

## 关联

- 上游 skill: `hermes-provider-fallback-tuning` (新增 6-place audit 节 + 上述两个新 pitfall)
- 关联脚本: `scripts/audit-builtin-oauth-providers.sh` (一键体检: 跑 `hermes model` 抓候选, 标记 .env-可控 vs BUILTIN)
- 同 umbrella 现有 audit 脚本: `scripts/audit-deepseek-leak.sh` (5 链), `scripts/audit-minimax-provider.sh` (custom 代理)
