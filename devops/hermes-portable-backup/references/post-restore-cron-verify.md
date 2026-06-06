# 恢复后 Cron Jobs 静默丢失

## 现象

2026-06-06 用户反馈：昨晚 23:07 配好的 anysearch + last30days 定时搜索 cron job 凭空不见了。

## 根因

GitHub 备份/恢复流程中 `cron/jobs.json` 可能被：
- 还原脚本覆盖（restore 覆盖了整个 cron 目录）
- jobs.json 格式解析差异（dict vs list 格式混用）
- 备份时 jobs.json 本身就只存了部分数据

## 修复

恢复后**必须**验证：
```bash
python3 -c "
import json
with open('$HOME/.hermes/cron/jobs.json') as f:
    data = json.load(f)
jobs = data.get('jobs', data)
print(f'Total cron jobs: {len(jobs)}')
for j in jobs:
    if isinstance(j, dict):
        print(f'  {j.get(\"name\",\"\")}')
"
```

与用户回忆的预期数量对比，不匹配就立刻补建。

## 触发信号

- 用户说"cron 配置没了" / "定时任务不见了" / "昨晚配的 XXX 跑不了"
- 刚跑完 `hermes_restore_one.sh` 或 `hermes_restore.sh`
- 刚做了 `config.yaml` 迁移

## 补救

回忆用户说的 cron 配置内容，用 `cronjob(action='create')` 重新建立。
