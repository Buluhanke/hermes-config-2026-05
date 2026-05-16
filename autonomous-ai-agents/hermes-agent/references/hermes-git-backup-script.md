# Hermes Git Backup Script

每小时自动将 `~/.hermes` 配置变更推送到 GitHub。

## 脚本内容

```bash
#!/bin/bash
cd ~/.hermes || exit 0

# 检查是否有变更
git diff --quiet && git diff --cached --quiet
if [ $? -eq 0 ]; then
    # 无变更，静默退出
    exit 0
fi

# 添加所有变更并提交
git add -A
git commit -m "auto backup $(date '+%Y-%m-%d %H:%M')" > /dev/null 2>&1

# 先拉取远端变更再推送（解决多机冲突）
git pull --rebase origin main > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # rebase 冲突，中止，等下次 cron 重试
    exit 1
fi

git push origin main > /dev/null 2>&1
```

## 使用方式

```bash
# 创建 cron 任务（no_agent=True，省略 repeat 参数）
cronjob(action='create', name='hermes-config-backup', schedule='every 1h', script='hermes-git-backup.sh', no_agent=True)
```

## 前提条件

- `~/.hermes` 已是 Git 仓库，remote 指向 GitHub HTTPS URL（含 Token）
- 当前用户对仓库有 push 权限

## 验证

```bash
# 确认 cron 任务存在
cronjob(action='list')

# 手动触发测试
cronjob(action='run', name='hermes-config-backup')
```
