# 主动进化 Cron Jobs 配置

## jobs.json 路径
`~/.hermes/cron/jobs.json`

## 当前任务列表（2026-05-18 更新）

| job_id | 名称 | schedule | deliver | last_status |
|--------|------|----------|---------|-------------|
| `8834c6edfa07` | 自我进化-夜间学习 | `0 2 * * *` | qqbot | error |
| `901badf20e32` | 数字分身-早班 | `30 8 * * *` | qqbot | ok |
| `40bdf8d837b0` | 每日晨间巡检 | `0 8 * * *` | qqbot | ok |
| `46b1467938bd` | 语音缓存清理 | `0 3 * * *` | local | ok |
| `f16b1c636b6c` | n8n工作流每日备份 | `0 4 * * *` | local | ok |
| `75bb2ae40880` | skills仓库自动同步 | `every 60m` | local | ok |
| `ebf6eec5973d` | Hermes配置自动同步 | `0 22 * * *` | local | ok |
| `414cab21d033` | 每日Wiki体检 | `0 8 * * *` | qqbot:EC16BFF... | ok |
| `a652f13a695d` | 后台自我观持续巡检 | `*/30 * * * *` | local | ok |
| `6bcbc234d12f` | Hermes真人工化学习巡检 | `0 3 * * *` | local | error |

**注意**：`8834c6edfa07` 和 `6bcbc234d12f` last_status 为 error，但 delivery target 是 qqbot，不是主要进程报警。

## 进化任务分层（2026-05-15确立）

### 白天碎片巡检
- schedule: `0 */2 * * *`（8:00/10:00/12:00/14:00/16:00/18:00/20:00/22:00）
- 执行前查 session_search，用户空闲才执行
- 轻量快搜，≤5分钟，轮换方向
- 重大突破QQ通知，普通发现静默存档

### 夜间深度学习
- schedule: `0 2 * * *`
- 全网深度搜索 + 浏览器AI对话
- 结合已有技能，锚定真人化路线

## 编辑注意

jobs.json 内 prompt 字段存储为 Unicode 转义形式。不要用 patch 工具直接编辑，会因转义匹配失败。

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

## 真人化目标锚定（2026-05-15确立）

每次进化搜索必须围绕：
1. 屏幕全域感知（95%差距）→ 最高优先
2. 验证码对抗（100%差距）
3. 类人操作节奏（80%差距）
4. 移动端操控（100%差距）
5. 多步骤业务闭环（50%差距）

进化不跑偏 = 始终服务真人化终极目标
