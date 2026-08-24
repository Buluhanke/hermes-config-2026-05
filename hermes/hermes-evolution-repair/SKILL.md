---
name: hermes-evolution-repair
description: Hermes进化循环断点自查：free_bytes漏$、内存守卫阈值、cron config-drift pin。
triggers:
  - 进化循环断了
  - night-learning 报错
  - 每日自学没跑
  - 深度进化梳理
---

# Hermes 进化循环自检与修复

## 三类已知断点

| 断点 | 症状 | 根因 |
|------|------|------|
| shell 变量在 python 内漏 `$` | `NameError: name 'free_bytes' not defined`，`set -e` 直接挂死 | `${free_bytes}` 写成 `free_bytes` |
| 内存守卫阈值过高 | `空闲 XGB < 4GB，仍不足 4GB，跳过`，每轮被挡 | macOS 常驻空闲 ~2GB，4GB 阈值永远达不到 |
| cron config drift 守卫 | `Skipped to prevent unintended spend`，agent cron 静默失败 | provider/model 变了但 cron 没 pin |

---

## 自查步骤

### 1/3 — free_bytes 漏 $ 检查（5秒）

```bash
grep -n 'free_bytes' ~/.hermes/scripts/idle_learning_wrapper.sh
# 正确：print(${free_bytes} / 1024**3)
# 错误：print(free_bytes / 1024**3)  ← 漏 $

# 修复
sed -i '' 's/print(free_bytes/print(\${free_bytes}/g' ~/.hermes/scripts/idle_learning_wrapper.sh
```

### 2/3 — 内存守卫阈值 4GB→2GB（5秒）

```bash
grep -n 'free_gb < ' ~/.hermes/scripts/idle_learning_wrapper.sh
# 有输出则改
sed -i '' 's/free_gb < 4/free_gb < 2/g' ~/.hermes/scripts/idle_learning_wrapper.sh
```

### 3/3 — cron config-drift pin（10秒）

```bash
# 查所有 agent 模式 cron
hermes cron list
# 对非 no_agent 的 cron，pin 当前 provider/model
hermes cron edit <job_id> --provider <当前provider> --model <当前model>
```

---

## 验证

```bash
# idle_learning 实跑
cd ~/.hermes && bash scripts/idle_learning_wrapper.sh >/tmp/il_test.log 2>&1
echo "EXIT=$?"; tail -5 /tmp/il_test.log
# 预期：EXIT=0，含 "fact_store 统计" + "wrapper 完成"

# 自学 cron 手动触发
hermes cron run <job_id>
# 预期：delegation_id 返回，状态 success

# 最新日志
ls -t ~/.hermes/cron/output/idle_learning/*.log | head -1 | xargs tail -5
```

## 坑点

- macOS 无 `timeout` 命令，脚本里禁用
- `set -e` + 管道中 python 报错：python 非 0 不会传管道退出码，用 `|| echo` 兜底
- self_research_wrapper.sh 必须是空脚本（内容清空），cron agent 模式直接加载 skill
