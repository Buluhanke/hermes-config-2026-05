# Hermes Backup System

备份体系文档，对 hermes-backup 备份的完善和说明。

## 备份范围

| 类型 | 路径 | 说明 |
|------|------|------|
| 配置 | `~/.hermes/config.yaml` | Hermes 主配置文件 |
| 环境变量 | `~/.hermes/.env` | API密钥等敏感信息 |
| Skills | `~/.hermes/skills/` | 所有技能模块 |
| 脚本 | `~/.hermes/scripts/` | 自定义脚本 |
| 记忆 | `~/.hermes/memory/` | 对话记忆数据 |
| 浏览器Cookie | - | **无法自动迁移，需单独处理** |

## 备份策略

```bash
#!/bin/bash
# hermes-backup.sh

BACKUP_DIR="~/hermes-backup"
DATE=$(date +%Y-%m-%d)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 压缩备份
tar -czf $BACKUP_DIR/hermes-config-$DATE.tar.gz \
  ~/.hermes/config.yaml \
  ~/.hermes/.env \
  ~/.hermes/skills/ \
  ~/.hermes/scripts/ \
  ~/.hermes/memory/

# Git同步（私有仓库）
cd $BACKUP_DIR
git add .
git commit -m "Backup $DATE"
git push origin main

# 清理30天前本地备份
find $BACKUP_DIR -name "hermes-config-*.tar.gz" -mtime +30 -delete
```

## 恢复步骤

1. 克隆 hermes-backup 私有仓库
2. 解压配置到 `~/.hermes/`
   ```bash
   tar -xzf hermes-config-YYYY-MM-DD.tar.gz -C ~/
   ```
3. 重新扫码登录 1688（Cookie 无法迁移，需重新认证）
4. 重启 Hermes 服务
   ```bash
   launchctl kickstart -k gui/$(id -u)/com.hermes.agent
   ```

## 自动化

- **Cronjob**: 每日 22:00 自动执行备份脚本
  ```bash
  0 22 * * * /Users/aimac/hermes-backup/hermes-backup.sh
  ```
- **本地保留**: 最近 30 天备份（自动清理）
- **远程存储**: GitHub 私有仓库永久保存

## 仓库分工

| 仓库 | 类型 | 内容 |
|------|------|------|
| `hermes-config-2026` | 公开仓库 | 文档模板、标准化配置示例 |
| `hermes-backup` | 私有仓库 | 实际配置、密钥、Skills |

- **公开仓库**: 存放规范化的配置模板和文档，不含敏感信息
- **私有仓库**: 存放实际运行的配置、API密钥、自定义Skills

## 注意事项

1. **Cookie 迁移**: 浏览器 Cookie 因安全限制无法自动迁移，换设备后需重新扫码登录 1688
2. **加密存储**: `.env` 中的敏感信息建议进一步加密后再提交到私有仓库
3. **定期验证**: 每月执行一次恢复演练，确保备份可用