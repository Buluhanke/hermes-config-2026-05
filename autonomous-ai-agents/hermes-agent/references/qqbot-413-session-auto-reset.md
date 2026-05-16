# QQ Bot 413 / Session Auto-Reset Troubleshooting

用户症状: QQ 机器人反复提示 ⚠️ Request payload too large (413) + 🔄 Session auto-reset

## 诊断流程

### 1. 确认错误来源

413 错误有两种可能:

- **LLM Provider 413** — DeepSeek API 返回 HTTP 413, 因为请求体中的对话历史太大
  - 症状: agent.log 中出现 "413 compression attempt 1/3" + run_agent.py 触发上下文压缩
  - 修复: 减少每次对话的产出量

- **QQ Bot API 413** — 发送给 QQ 平台的消息超过限制 (MAX_MESSAGE_LENGTH=4000)
  - 症状: QQ adapter 的 `_api_request()` 抛出 `"QQ Bot API error [413]"`
  - 修复: 检查 format_message()/truncate_message() 是否正确切割长消息

### 2. 检查定时任务 (常见陷阱)

用户说"一直提示"时，**先查 cron 任务**——它们可能每 N 分钟跑一次并持续报错:

```bash
cronjob(action='list')
```

常见问题:
- "QQ Bot 健康检查" cron 每30分钟跑一次，因 session 太大不断返回 413
- 用户看到的是**历史多次错误提示**, 不是当前单一请求的问题
- 移除或暂停有问题的 cron: `cronjob(action='remove', job_id='xxx')`

### 3. 检查 session 文件大小

如果 cron 反复执行失败, session 文件会越来越大:

```bash
ls -la ~/.hermes/sessions/ | sort -k5 -n | tail -10
```

大于 100KB 的 session 文件可能已异常膨胀。清理:

```bash
rm -f ~/.hermes/sessions/session_cron_<job_id>_*.json
```

### 4. 重启网关

杀掉旧进程, 启动新网关, 清空缓存 session:

```bash
# 查网关 PID
ps aux | grep hermes_cli | grep gateway | grep -v grep | awk '{print $2}'
# 杀掉
kill <PID>
# 重新启动
hermes gateway run --replace --daemon
```

### 5. 加大压缩模型的 context_length (最关键)

这是本 session 发现的核心根因：**auxiliary.compression.context_length 默认只有 131072 (128K)**。

当主模型支持 1M context 时，对话很容易超过 128K。此时压缩模型**自己都塞不下对话内容**，`_compress_context()` 返回原消息(未压缩)，压缩失败。3次尝试后 `compression_exhausted=True`。

**修复**：将 `auxiliary.compression.context_length` 设为主模型 context 的 80% 左右：

```yaml
auxiliary:
  compression:
    context_length: 819200  # 800K, 匹配 deepseek-v4-flash 的 1M context
```

这样压缩模型有足够空间处理完整对话，压缩才能生效。

### 6. 减少对话产出

如果问题来自上游 agent (如 supply-agent-v11) 输出太大:

- 减少搜索结果数量 (如 max_results=25→10, check_detail=8→4)
- 精简输出格式 (截断过长的名称/规格/链接，单商品从6行压缩到2-3行)
- 注意：QQ 机器人里 `/new` 虽然有效，但 session 在报错时已**自动重置**，用户不需要手动 `/new`

### 7. `/new` 在 QQ 机器人的特殊行为

在 CLI 中 `/new` 是手动清 session 的方式。但在 QQ 机器人网关中：

1. 当 `compression_exhausted=True`，gateway **自动调用了** `reset_session()`（gateway/run.py line 6616）
2. 然后才把包含 "💡 Try /new" 的响应发回用户
3. 用户收到消息时 session 已经是新的了，再打 `/new` 只是又重置一次空 session

所以用户看到 `/new` "没效果"——不是命令不灵，而是 session 已自动重置，不需要再手动操作。

### 深入理解: 代码流程

1. `run_agent.py` line 12543: LLM provider 返回 413 → 触发压缩, 显示 "⚠️ Request payload too large (413) — compression attempt 1/3"
2. `run_agent.py` line 12561: 压缩后 payload 仍过大 → "❌ Payload too large and cannot compress further"
3. `run_agent.py` line 12533-12542: `compression_exhausted=True` 返回给 gateway
4. `gateway/run.py` line 6611-6626: Gateway 检测到 `compression_exhausted` → auto-reset session + 追加 "🔄 Session auto-reset — the conversation exceeded the maximum context size" 到响应

### 配置调优

#### 阶段1：调低阈值（效果有限）

减少 compression 触发频率:

```yaml
compression:
  threshold: 0.13    # 默认 0.50, 但主模型 1M context 时 0.50=500K 才触发
                     # 压缩模型只有 131K context, 设 0.13=131K 让压缩在能处理范围内触发
  target_ratio: 0.20
  protect_last_n: 20
```

#### 阶段2：关闭 compression（最终解法）

**经过 2026-05-06 实测**：即使 `auxiliary.compression.context_length: 819200`（800K）已设置，deepseek-v4-flash 压缩模型在处理超长 QQ 对话历史时仍然返回 413。

**根因**：QQ 会话历史太长 + 压缩模型本身也有上限 → 即使调整 context_length 也无法解决。

**最终解法**：关闭 compression，靠 session_reset 兜底：

```yaml
compression:
  enabled: false
  threshold: 0.13
  target_ratio: 0.2
  protect_last_n: 20
  hygiene_hard_message_limit: 400

session_reset:
  idle_minutes: 120   # 原来 1440（24小时）太长，QQ 对话频繁导致 context 快速膨胀
  mode: both
```

**为什么关闭比调优更可靠**：compression 的目的是在 context 快满时压缩历史，但如果历史本身就已经大到压缩模型塞不下，压缩动作本身就会失败。关闭后依赖 idle 自动重置，反而不会产生 413 错误。

**重启生效**：`hermes gateway restart`
