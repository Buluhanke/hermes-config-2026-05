# Hub 安装工作流 (Hermes Skills Hub)

> 沉淀自 2026-06-29 cron 任务实战 — `hermes skills search/browse/install/inspect/audit` 完整 CLI 工作流 + 安全 verdict 决策树。

## 1. 检索（search / browse）

### 按关键词搜（多源聚合 74612 skills）

```bash
# 模糊关键词
hermes skills search --limit 5 "screen understanding"

# 官方名/品牌名（命中率最高）
hermes skills search --limit 5 "1password"
hermes skills search --limit 5 "dspy"
hermes skills search --limit 5 "docker-management"
```

### 浏览全貌（按 source 过滤）

```bash
# 全部源
hermes skills browse --size 50

# 仅官方源
hermes skills browse --source official --size 50

# 单源
hermes skills browse --source skills-sh --size 30
hermes skills browse --source clawhub --size 30
```

支持的 source: `all | official | skills-sh | well-known | github | clawhub | lobehub | browse-sh`

## 2. 预览（inspect）

装之前**永远先 inspect**，看 SKILL.md + 文件清单：

```bash
hermes skills inspect "official/security/1password"
hermes skills inspect "skills-sh/charleswiltgen/axiom/axiom-macos"
```

## 3. 安装（install）

### 三种安装结果

| 情况 | 输出 | 行动 |
|---|---|---|
| 全新安装 | `Installed: <name>` + `Files: ...` | 啥都不用做 |
| 已装 | `Warning: '<name>' is already installed at <path>` | 不重装，除非 hub 状态脱节（见 pitfall 6） |
| 拦 | `Decision: BLOCKED — ...` | 看 verdict（见 §4） |

### 关键 flag

```bash
# cron / 脚本 / 无 TTY 环境 — 必加
hermes skills install --yes <identifier>

# 强制绕过 caution verdict
hermes skills install --force --yes <identifier>

# 装到指定 category 子目录
hermes skills install --category my-cat <identifier>

# 自定义 name
hermes skills install --name my-name <identifier>

# 从 URL 直接装
hermes skills install --yes "https://raw.githubusercontent.com/.../SKILL.md"
```

**`--yes` vs `--force`**：正交两个 flag。
- `--yes` = 跳过确认 prompt
- `--force` = 绕过安全扫描 verdict

## 4. 安全 verdict 决策树

```
fetch + scan
  ↓
[SAFE]       → ALLOWED
[caution]    → BLOCKED, 可 --force 绕过
[dangerous]  → BLOCKED, --force 也拦不住
```

### 典型 findings 类型（caution 级别）

- `privilege_escalation` — 脚本含 `sudo` / `killall -9` / 改 /Library/Keychains
- `supply_chain` — `curl -sL https://x/install.sh | bash` 模式
- `persistence` — 写 `~/.bashrc` / `~/.zshrc` / IDENTITY.md / SOUL.md

### 优先级（按 trust）

1. **official**（★ official，Nous Research 维护）— verdict 永远 SAFE
2. **skills.sh** — 社区索引，质量参差，多数 caution
3. **clawhub** — 社区源，dangerous 比例最高
4. **github / well-known / lobehub** — 各有侧重

### 守则

- community skill 即便 `--force` 装上，**手动 review `scripts/` 子目录**再决定真用
- dangerous 跳过，别装
- caution → 装可以，但加 `--force` 后必须 README 注释一条 "此 skill 触发 N 个 caution finding"

## 5. 审计 / 修复（audit / repair）

```bash
# 检查 hub 状态 vs 本地状态
hermes skills audit

# 单个官方 skill 重新拉（保留原副本为 backup）
hermes skills repair-official <name> --restore

# 全量重拉所有官方 skill
hermes skills repair-official all
```

**典型症状**：`Warning: <name> — path missing`（hub 元数据存在但本地副本被清理/丢失）。
**根因**：`hermes update` 后 / `.archive/` 清理时误删 / 跨 profile 切换。
**修法**：`hermes skills install --force <identifier>` 重新拉取。

## 6. 5 个能力类固定目标集

每天 cron 采集时按这 5 类各搜 1-2 次：

| 能力类 | 关键词候选 | 推荐 skill |
|---|---|---|
| 真屏幕理解 / 多模态 | `screen understanding`, `vision`, `multimodal` | `axiom-macos`, `clip` |
| 离线工具 / 本地服务 | `docker`, `service`, `mcp` | `docker-management`, `fastmcp`, `hermes-s6-container-supervision` |
| 安全 / 凭据 / 隐私 | `1password`, `credential`, `secret` | `1password`, `agentmail` |
| 性能监控 / 内存治理 | `performance`, `memory monitor` | `qdrant`, `faiss` (向量层), system monitor 类 community skill |
| 跨平台 / 跨渠道 | `cross-platform`, `mcp`, `container` | `fastmcp`, `hermes-s6-container-supervision` |

**铁律**：5 个能力类每个必须有处理结果（已装 / 候选落盘 / 明确写"为什么没找到"），不许 SILENT。

## 7. 候选落盘 (skills_pending.json)

找不到的 skill URL 写到 `~/.hermes/skills_pending.json`：

```json
[
  {
    "query": "memory monitor",
    "candidates": [
      {"name": "nix-memory", "url": "https://...", "blocked_reason": "dangerous verdict — supply_chain curl|bash"},
      {"name": "system-monitor", "url": "https://...", "status": "pending"}
    ],
    "scanned_at": "2026-06-29T03:00:00"
  }
]
```

## 8. 实战 2026-06-29 cron 跑出

| 能力类 | 候选 | verdict | 结果 |
|---|---|---|---|
| 安全/凭据 | 1password | SAFE | ✅ 装 |
| Docker | docker-management | SAFE (已预装) | ✅ 跳过 |
| ML 自进化 | dspy | SAFE (已预装) | ✅ 跳过 |
| 屏幕理解 | axiom-macos | caution (3 findings) | ✅ --force 装 |
| macOS 自动化 | macos-automation | caution (2 findings) | ✅ --force 装 |
| 内存治理 | nix-memory | dangerous | ❌ 跳 |
| 系统清理 | macos-cleaner | dangerous (41 findings) | ❌ 跳 |
