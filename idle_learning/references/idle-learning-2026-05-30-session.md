# Idle Learning 2026-05-30 Session

**执行时间**：2026-05-30 ~07:00
**执行模式**：cron scheduled job (idle_learning skill)
**触发条件**：连续5分钟无用户指令

## 网络状态
- github.com: **blocked**
- news.ycombinator.com: **blocked**
- hacker-news.firebaseio.com: **OK** ✅

## 本地 Ollama 模型状态（重大发现）

```bash
$ curl -s --max-time 8 http://127.0.0.1:11434/api/tags
```
**结果**：仅 2 个模型存活
```
qwen2.5:1.5b | 0.92 GB
qwen3-vl:2b  | 1.76 GB
```

**重大异常**：
- `ahmadwaqar/smolvlm2-agentic-gui:latest` ❌ 已从本地消失
- `nomic-embed-text:latest` ❌ 已从本地消失

**Ollama 服务状态**：正常运行（PID 1368，进程驻留）
**根因**：Ollama API 本身正常，模型文件被清理（非服务崩溃）

## screen_watcher 链路状态
- screen_watcher 进程：**运行中** ✅
- current.png 更新：**正常**（15:49）
- auto_execute DRY_RUN：**正常**（302 条记录）
- handler 场景分析：**异常**（smolvlm2 模型缺失，Connection refused）

## 关键教训

1. **Ollama 服务活着 ≠ 模型还在**：Ollama 进程运行正常，但模型可以被删除
2. **检查模型状态必须用 curl**：`curl http://127.0.0.1:11434/api/tags` 比 `ollama list` CLI 更可靠
3. **hermes venv python3 无 ollama 模块**：用 `/usr/local/bin/python3` 代替
4. **github.com blocked 无法恢复模型**：需等网络恢复后执行 `ollama pull ahmadwaqar/smolvlm2-agentic-gui:latest`

## 待办
- [ ] github.com 恢复后重新 pull smolvlm2-agentic-gui
- [ ] 确认是否有定时任务/脚本清理了本地模型（防止再次丢失）
- [ ] 考虑定期备份关键模型文件
