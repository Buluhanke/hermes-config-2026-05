# Hermes 灾难恢复与备份

## 备份策略

### GitHub 仓库
| 仓库 | 内容 | 频率 |
|------|------|------|
| `hermes-config-2026-05` | 配置文件 + Chrome数据 + n8n工作流 | 自动每60分钟 |
| `hermes-skills` (main分支) | Skills库（全部技能定义） | 手动 |
| `hermes-skills` (obsidian-backup分支) | Obsidian笔记库 | 手动 |

### 关键数据路径
```
~/.hermes/                    # Hermes配置（GitHub: hermes-config-2026-05）
~/.hermes/skills/             # Skills库（GitHub: hermes-skills）
~/Obsidian/迅龙贸易/          # Obsidian笔记（GitHub: hermes-skills#obsidian-backup）
~/n8n_data/                   # n8n工作流（GitHub: hermes-config-2026-05/.n8n_backup）
~/.hermes/audio_cache/        # 语音缓存（本地，无需备份）
```

## n8n 备份细节

**备份内容**：config + database.sqlite + nodes/（不含 crash.journal / sqlite-shm/wal / storage / n8nEventLog.log）

**恢复步骤**：
```bash
# 克隆配置
git clone https://github.com/Buluhanke/hermes-config-2026-05.git ~/.hermes

# 恢复n8n
cp hermes-config-2026-05/.n8n_backup/* ~/n8n_data/

# 重启n8n容器
docker restart hermes-ai-n8n-1
```

**n8n 数据卷挂载**（docker inspect 确认）：
```
/Users/aimac/n8n_data -> /home/node/.n8n
```

## 每日自动备份 Cronjob

| Job ID | 名称 | 频率 | 脚本 |
|--------|------|------|------|
| b60a398e93fa | hermes-config-backup | 每60分钟 | hermes-git-backup.sh |
| 008fce294402 | 每日凌晨3点同步配置 | 每天03:00 | sync-hermes-backup.sh |
| f16b1c636b6c | n8n工作流每日备份 | 每天04:00 | backup_n8n.sh |
| 46b1467938bd | 语音缓存清理 | 每天03:00 | cleanup_audio_cache.sh |

## 恢复检查清单

1. 克隆 `hermes-config-2026-05` → `~/.hermes`
2. 克隆 `hermes-skills` → `~/.hermes/skills`（覆盖现有）
3. 从 `hermes-config-2026-05/.n8n_backup` 恢复 n8n 工作流
4. 从 `hermes-skills` 的 `obsidian-backup` 分支恢复 Obsidian 笔记
5. 重启 n8n 容器
6. 验证 Hermes Agent 可运行

## 注意事项

- Chrome调试实例通过 launchd 自启动，端口9333
- 1688登录cookies在 `~/.hermes/1688_cookies.json`，已包含在Git备份中
- Skills库无.gitignore，大量.DS_Store也被提交，不影响恢复
