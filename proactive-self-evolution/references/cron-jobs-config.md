# 主动进化 Cron Jobs 配置

## jobs.json 路径
`~/.hermes/cron/jobs.json`

## 当前任务状态（2026-05-27 确认）

| job_id | 名称 | schedule | deliver | last_status |
|--------|------|----------|---------|-------------|
| `8834c6edfa07` | 空闲自学 | `0 2 * * *` | qqbot | ok（已修复） |
| `901badf20e32` | 数字分身-早班 | `30 8 * * *` | qqbot | ok |
| `40bdf8d837b0` | 每日晨间巡检 | `0 8 * * *` | qqbot | ok |
| `46b1467938bd` | 语音缓存清理 | `0 3 * * *` | local | ok（已修复） |
| `f16b1c636b6c` | n8n工作流每日备份 | `0 4 * * *` | local | ok |
| `75bb2ae40880` | skills仓库自动同步 | `every 60m` | local | ok |
| `ebf6eec5973d` | Hermes配置自动同步 | `0 22 * * *` | local | paused |
| `414cab21d033` | 每日Wiki体检 | `0 8 * * *` | qqbot | ok |
| `a652f13a695d` | 后台自我观察扫描 | `*/30 * * * *` | local | ok |
| `6bcbc234d12f` | Hermes真人工化学习巡检 | `0 3 * * *` | local | ok（已修复） |
| `64a85a3294f5` | Hermes每日社区学习 | `0 */6 * * *` | qqbot | ok |

## 已知失败任务（2026-05-27 更新）

**最常见根因：cron 环境 HOME 变量为空**

cron 调度器启动时 HOME=/（root），脚本中 `~/.hermes/` 展开为 `/.hermes/`，权限不足写入失败。
表现：手动运行脚本正常，但 cron 状态 error，日志显示 `Permission denied` 或路径变成 `/.hermes/...`。

修复：脚本内所有路径用 `${HOME:-/Users/aimac}` 替代 `~` 和 `$HOME`。
```bash
# 错误
LOG="${HOME}/.hermes/logs/evolution.log"
OBSIDIAN=~/Obsidian/...

# 正确
LOG="${HOME:-/Users/aimac}/.hermes/logs/evolution.log"
OBSIDIAN="${HOME:-/Users/aimac}/Obsidian/..."
```

验证命令：`env -i HOME= PATH=$PATH bash ~/.hermes/scripts/xxx.sh`

**jobs.json 编辑注意**：prompt 字段存储为 Unicode 转义，不要用 patch 直接编辑。

正确方式：
```python
import json
with open('/Users/aimac/.hermes/cron/jobs.json') as f:
    data = json.load(f)
# 修改 data['jobs']
with open('/Users/aimac/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## 进化存储路径
- ~/Vision_Lab/ — 工具/技能方向
- ~/Brain_Lab/ — 思路/方法论方向

## 真人化目标锚定

1. 屏幕全域感知（95%差距）→ 最高优先
2. 验证码对抗（100%差距）
3. 类人操作节奏（80%差距）
4. 移动端操控（100%差距）
5. 多步骤业务闭环（50%差距）
