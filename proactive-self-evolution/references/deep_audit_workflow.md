# 系统深层检查清单

定期执行，防止系统腐化导致变慢/卡死/死循环。

## 执行时机
- 重大变更后（清理、升级、迁移）
- 用户说"检查一下"
- 每月底例行

## 检查维度

### 1. Cron任务健康
```
hermes cron list
```
- 检查 `last_status` 列：全部应为 `ok`
- error状态的job → 立即修复或删除
- 检查引用的skill是否存在（缺失skill会阻塞agent模式cron）

### 2. 孤儿脚本清理
scripts目录（`~/.hermes/scripts/`）中：
- 被cron直接引用的脚本（从cron list的Script:字段确认）
- 被其他脚本import/call的脚本
- screen_watcher.py / screen_trigger_handler.py 进程在跑 = 被使用
- 其余均为孤儿候选

孤儿脚本特征：
- 名称含 `bak`/`backup`/`old`/`test`
- 与其他脚本功能重复（如 `cleanup_audio_cache.sh` vs `cleanup_audio_cache`）
- cron没引用 + 进程没用 = 删

### 3. Git同步状态
```bash
cd ~/.hermes/skills && git status -sb
```
- ahead/behind 17 → 本地有未push的commit，先 `git push`
- [ahead N] → 有N个本地commit未同步
- 冲突先 `git fetch origin && git reset --hard origin/main`

### 4. 进程存活验证
```bash
pgrep -f "screen_watcher" && echo "✅" || echo "❌ 未运行"
curl -s --max-time 3 http://localhost:8899/v1/default/banks && echo "✅ hindsight" || echo "❌"
docker ps --format "{{.Names}} {{.Status}}" | grep -v Up
```

### 5. 大日志/临时文件
- 日志 > 50MB → 归档或截断
- `/tmp/hermes*` 临时文件过多 → 清理
- screenshots目录 > 100个文件 → 只保留最新10个

## 典型问题模式

| 症状 | 根因 | 修复 |
|------|------|------|
| Cron job error 128 | git push失败（ahead/behind冲突）| git reset --hard origin/main |
| skill缺失但cron有引用 | 删skill后cron未更新 | 删除该cron job |
| 凌晨死机 | screen_watcher无限重试+handler堆积 | 调长冷却时间+加休眠模式 |
| Gateway多PID冲突 | 重启时旧进程未完全退出 | kill -9旧PID |
| 自我优化跑不起来 | skill缺失/脚本路径错 | 检查skill存在性 |

## 快速完整检查（单命令）
```bash
hermes cron list | grep -E "error|ERROR" && echo "⚠️ 有错误" || echo "✅"
pgrep -f screen_watcher > /dev/null && echo "✅ screen_watcher" || echo "❌"
cd ~/.hermes/skills && git status -sb | grep -v "## main...origin/main$" && echo "⚠️ git不同步"
```
