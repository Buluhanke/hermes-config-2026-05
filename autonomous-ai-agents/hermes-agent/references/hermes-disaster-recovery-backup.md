# Hermes 灾难恢复与备份

## GitHub 仓库架构（2026-05-16 更新）

| 仓库 | 可见性 | 内容 | 大小 |
|------|--------|------|------|
| `hermes-backup` | **私有** | .env、auth.json、skills、scripts、launchd、perception.py | ~10MB |
| `hermes-config-2026-05` | 公开 | 配置文件模板 + 文档（已清理大文件） | ~28MB |
| `hermes-skills` | **私有** | skills 技能库同步镜像 | ~3MB |

**hermes-backup 是主力仓库**，包含所有敏感配置。换电脑只需 `bash ~/hermes-restore.sh`。

**清理记录（2026-05-16）**：`chrome-debug/`（299MB）、`audio_cache/`（492KB）、`config.yaml.bak.*` 已从 hermes-config-2026-05 移除并用 `git filter-branch` 重写历史。本地 pack 从 220MB 缩至 8.8MB，push 后 GitHub 显示大小延迟更新，实际新克隆 ~28MB。

## 备份策略

### GitHub 仓库
| 仓库 | 内容 | 频率 |
|------|------|------|
| `hermes-backup` | **完整备份**（.env、auth.json、skills、scripts、launchd） | 手动同步 |
| `hermes-config-2026-05` | 配置文件模板 + 文档（已清理大文件） | 自动每60分钟 |
| `hermes-skills` | Skills库 | 自动每60分钟 |

### 关键数据路径
```
~/.hermes/                    # Hermes配置（主力：hermes-backup 私有仓库）
~/.hermes/skills/             # Skills库
~/Obsidian/迅龙贸易/           # Obsidian笔记（GitHub: hermes-skills#obsidian-backup）
~/n8n_data/                   # n8n工作流（GitHub: hermes-config-2026-05/.n8n_backup）
~/.hermes/audio_cache/        # 语音缓存（本地，无需备份）
```

### 恢复脚本
- `~/hermes-restore.sh` — 一键恢复（克隆 hermes-backup + hermes-agent + 安装依赖）
- `~/sync_hermes.sh` — 同步本地修改到 hermes-backup 私有仓库

## n8n 备份细节

**⚠️ 关键陷阱：SQLite WAL 模式**

n8n 使用 SQLite WAL 模式，运行时 `database.sqlite` 只有 ~600KB，真实数据在 `database.sqlite-wal`（可达 4MB+）。直接备份 sqlite 文件会丢失未合并的 WAL 数据。

**✅ 正确流程：先做 Checkpoint，再备份**
```python
import sqlite3
conn = sqlite3.connect('/Users/aimac/n8n_data/database.sqlite')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')  # 合并WAL并截断
conn.execute('VACUUM')  # 压缩数据库
conn.close()
```

**备份脚本**：`~/.hermes/scripts/backup_n8n.sh`（已内置 checkpoint 逻辑）

## 恢复检查清单

1. `bash ~/hermes-restore.sh`
2. 克隆 `hermes-skills` → `~/.hermes/skills`（覆盖现有）
3. 从 `hermes-config-2026-05/.n8n_backup` 恢复 n8n 工作流
4. 重启 n8n 容器

## 注意事项

- Chrome调试实例通过 launchd 自启动，端口9333
- 1688登录cookies在 `~/.hermes/1688_cookies.json`，已包含在Git备份中
- **1688 Cookie 无法迁移**：Chrome Cookie 加密存储，换电脑需重新扫码登录1688一次
