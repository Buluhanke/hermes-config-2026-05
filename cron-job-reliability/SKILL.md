---
name: cron-job-reliability
description: "cron可靠化 排障 last_status=error wrapper实跑验证。Use when 定时任务没跑静默失败或新建可靠job"
triggers:
  - cron job 不跑 / cron job 失败 / cron 没有执行
  - LLM 偷懒 / 写报告不执行 / 只说不做
  - wrapper 脚本 / cron 改成 script 模式
  - subprocess 超时 / 命令卡住 / timeout
  - 外部 API 限速 / arxiv rate limit / 降级策略
  - cron job 改成直跑脚本
  - no_agent=true script=
pitfalls:
  - name: LLM cron agent 偷懒写报告
    description: |
      当 cron job 只有 prompt 没有 script 时，Hermes 调度器会启动 LLM agent 执行 prompt。
      LLM agent 遇到复杂任务会偷懒：只写分析报告，不真正执行脚本命令。
      症状：cron output 里全是 Markdown 报告，没有实际的 python3/cd 命令执行记录。
      诊断：看 cron output 的内容，有## 本轮做了什么这种报告格式 = LLM 在写报告。
    fix: |
      改用 no_agent=true + script=<wrapper.sh>。让脚本直跑，不走 LLM。
      cronjob update 后立即手动跑一遍验证。
  - name: subprocess 卡死阻塞整轮 orchestrator
    description: |
      一个 subprocess.run 卡住（如 cve_scan 查 493 个包 x API 调用），
      导致整个 orchestrator 超时退出，其他方向扫描全跳过了。
      症状：ABCD 方向只看到 A，其他 B/C/D 全 missing。
    fix: |
      用 threading + join(timeout) 给每步独立超时，超时就标记状态并继续。
      不要让单个慢命令阻塞整轮。
  - name: 外部 API 限速导致整轮超时
    description: |
      arXiv API Rate exceeded 后 urllib/curl 都会 retry 直到超时，
      导致 B 论文方向卡住 30s+，影响整轮 orchestrator。
    fix: |
      缓存优先策略：1小时内用缓存，API 失败降级读过期缓存。
      curl 加上 --max-time 单次超时控制。
  - name: wrapper 脚本没有 shebang 或不可执行
    description: |
      新建 wrapper.sh 但忘记 chmod +x，或路径写错。
      症状：cron 触发时 Permission denied 或 not found。
    fix: |
      创建后立即 chmod +x + 手动跑一遍验证。
  - name: fact_store 路径不一致
    description: |
      多个脚本指向不同的 fact_store 路径：
      - ~/.hermes/memory/fact_store.db（不存在）
      - ~/.hermes/memories/fact_store.md（Markdown，非 DB）
      - ~/.hermes/memory_store.db（正确）
      症状：batch_facts_from_log 写入了，但 fact_decay 读不到。
    fix: |
      统一用 ~/.hermes/memory_store.db。Schema: fact_id, content, category, tags,
      trust_score, retrieval_count, helpful_count, created_at, updated_at。
      created_at/updated_at 存 float timestamp 或 ISO 字符串都要能解析。
  - name: cron job 修复后没有立即验证
    description: |
      改了 cron job 配置（script/no_agent）但没有手动触发验证，
      等到下次 schedule 时间才发现配置写错了。
    fix: |
      每次修改 cron job 后立即手动 run 一次，看 output 是否符合预期。
      用 cronjob(action=list) 检查 script 字段和 no_agent 字段是否都正确。
  - name: 空转输出（phantom output）
    description: |
      cron wrapper 报"✅ 处理 N 条 / 改动 X 个 domain / auto skill: Y generated"，
      数字漂亮但没有任何文件实际落地。
      诊断：self_model.json 报告"auto skill: 12"但 skills/auto-generated/ 不存在；
      fact_store 报告"新写入 0 条"但 total count 没变。
      根因：脚本内部逻辑有条件跳过（如"已存在"就跳过），但退出码仍为 0。
    fix: |
      每轮结束后检查实际落地物：ls ~/.hermes/skills/auto-generated/、fact_store 行数、
      self_model.json 的 actual 文件内容。wrapper log 要包含落地物清单。
      在 orchestrator 阶段加 assert：预期的写操作必须有对应的文件验证。
  - name: 两套 cron 系统混淆（crontab vs Hermes cron）
    description: |
      Hermes 有两套独立的定时任务系统，极易混淆：
      ① crontab 系统任务（`crontab -l`，系统cron进程(pid 290)执行）
         路径：/usr/sbin/cron run as root
         脚本：~/.hermes/scripts/ 下的 shell/python 脚本
         日志：各自独立的 log 文件（如 logs/self_evolution.log）
      ② Hermes cron 任务（`cronjob(action=list)`，Hermes 应用层调度）
         路径：Hermes 内部 DB 管理
         脚本：hermes cron 的 script= 字段指向 wrapper.sh
         日志：~/.hermes/cron/output/<name>/ 下
      症状：只查 Hermes cron 以为全覆盖，漏掉 crontab 里大量 1-6am 学习任务；
      或以为两套任务是同一个，困惑为什么日志对不上。
    fix: |
      诊断时要同时查两套：
        $ crontab -l                    # 系统层 crontab（1/2/3/4/5/6点任务）
        $ cronjob(action=list)          # Hermes 应用层 cron
        $ cat ~/.hermes/logs/*.log      # crontab 任务日志
        $ ls ~/.hermes/cron/output/     # Hermes cron 任务日志
      两套任务在内容上有重叠（如都有 idle_learning），但schedule不同。
      crontab 的 idle_learning_orchestrator.py 是旧版（4点），Hermes cron 的 idle_learning_wrapper.sh 是新版（1点ABCD自学）。
  - name: deep_research.sh Permission denied
    description: |
      crontab 里 deep_research.sh 报 Permission denied，
      原因：文件创建时没有 +x 权限。
      症状：logs/research.log 里出现 "/bin/sh: /path/to/script: Permission denied"
      影响：2点的深度研究任务完全静默失败。
    fix: |
      创建脚本后立即 chmod +x。
      也适用于其他 .sh/.py 脚本。
      crontab 里 python3 脚本（如 active_learner.py）也需要 +x。
  - name: fact_decay.py 只报不删（静默积累脏数据）
    description: |
      fact_decay.py 能正确识别 trust≤0.05 的过期 facts 并打印清单，
      但默认只打印不删除（除非加 --delete flag）。
      症状：fact_store 出现 age=20642d 这种不可能的数字（日期计算 bug 的脏数据），
      trust=0.000 但 fact_decay 只报告"可删除"而不实际删除。
      本次案例：id 97/98/99/109 四条 age=20642d，created_at 却是 2026-06-05。
      fact_decay 识别出来了但从未删除，连续跑了多轮还在。
    fix: |
      确认 fact_decay.py 有 --delete 或 --prune flag，直接加进 wrapper 调用。
      或在 orchestrator 阶段用 Python 直接 DELETE WHERE trust_score ≤ 0.05。
      定期抽检：SELECT fact_id, created_at, substr(content,1,50) FROM facts ORDER BY fact_id DESC LIMIT 10。
      健康的 fact 不应有 trust=0.000 或异常大的 age。
  - name: wrapper 传参与 script argparse 不匹配（静默失败）
    description: |
      wrapper 脚本调用 `python3 script.py scan --min-count 3`，
      但 script 的 argparse 不接受 subcommand（如 `scan`）或特定 flag（如 `--min-count`）。
      Python argparse 发现未知参数会立即 exit(2)，wrapper 继续执行 self-reinforce 后续步骤，
      最终 cron 任务报"ok"但实际上主脚本什么都没做。
      症状：wrapper log 里没有主脚本的输出（因为它根本没跑），只有后续步骤的输出。
      本次案例：auto_skill_scan_wrapper.sh 传 "scan --min-count 3"，
      但 auto_skill_from_failure.py 只接受 --dry-run / --days，scan 子命令被忽略 → 静默退出。
    fix: |
      写完 wrapper 后立刻手动跑一遍：`bash wrapper.sh && echo "exit: $?"`。
      检查主脚本是否真的执行了（看输出里有没有主脚本的标志字符串）。
      用 `python3 script.py --help` 确认它接受什么参数，再对照 wrapper 传的参数。
      最可靠的做法：wrapper 只传位置参数或无参数，主脚本用 argparse 调试模式（--help）验证。
  - name: hermes cron create 的 script 路径必须是纯文件名
    description: |
      `hermes cron create` 的 --script 参数只接受 ~/.hermes/scripts/ 下的纯文件名，
      不接受绝对路径（如 /Users/kk/.hermes/scripts/morning_briefing.sh）
      也不接受 ~ 相对路径。
      症状：create 报错 "Script path must be relative to ~/.hermes/scripts/. Got absolute or home-relative path"
      正确写法：`--script morning_briefing.sh`（不用加路径，Hermes 自动找 ~/.hermes/scripts/）
    fix: |
      --script 只传纯文件名，不要包含目录部分。
      创建前确认脚本已在 ~/.hermes/scripts/ 下。
  - name: --no-agent 是布尔 flag，不是 --no_agent=<value>
    description: |
      `hermes cron create` 的 --no-agent 是一个布尔 flag，不能写成 --no-agent=true 或 --no_agent=true。
      写成 `--no-agent true` 会把 "true" 当成下一个 positional argument（schedule）报错。
      正确做法是单独加 `--no-agent`，没有任何值。
    fix: |
      放在所有 flag 最后（或任何位置），单独写 `--no-agent`，不要赋值。
      正确：`hermes cron create "0 8 * * *" --name morning-briefing --script morning_briefing.sh --no-agent`
      错误：`--no-agent=true` / `--no_agent=true` / `--no-agent true`
  - name: 网络依赖型 cron 无网时每周 error 噪声
    description: |
      cron 脚本依赖外部网络（如 git pull 公网仓库、调用外网 API），当宿主网络不可达
      （直连被墙、代理需认证无凭据、VPN 断开）时整个脚本非零退出，cron last_status=error，
      每周/每天产生一条用户看不到的失败噪声，且实际没做任何事。
      本次案例：public-apis sync 每周一跑 `git pull origin master`，github.com 直连 SSL 中断、
      路由器 OpenClash 代理(192.168.8.1:7890)返回 407 需认证无凭据 → 持续 error。
    fix: |
      网络依赖型 cron 改成"连通性探测 + 优雅跳过"模式，无网时 exit 0（静默跳过，不产生 error）：
      ```bash
      # 1) 快速连通性探测（5s 超时），不可达就优雅跳过
      if ! curl -sS -m 5 -o /dev/null https://<目标host> 2>/dev/null; then
        echo "$(date '+%F %T') SKIP: <目标host> unreachable — skip sync"
        exit 0
      fi
      # 2) 可达才执行，失败仍 exit 0（避免 cron last_status=error）
      git pull origin master 2>&1 || { echo "WARN: pull failed despite reachable"; exit 0; }
      ```
      要点：探针用 curl 短超时（不要用 macOS 缺的 timeout 命令）；无网分支必须 exit 0 而非非零；
      即便可达时主命令失败也 exit 0，把"真错误"和"环境阻塞"区分开，避免无意义的 cron error。
      这是设计原则，不是环境故障——任何依赖外网的 cron 都应内置探针。
---

# Cron Job Reliability

## 核心原则

1. **能直跑脚本就不走 LLM**：脚本执行是确定性的，LLM 执行是不确定的。
2. **每步独立超时**：防止单步卡死导致整轮失败。
3. **失败有证据**：wrapper 把 stdout 写入文件，有迹可循。

## 标准 Wrapper 脚本模板

```bash
#!/bin/bash
# <name>_wrapper.sh — <用途>
set -e
HERMES_HOME="$HOME/.hermes"
OUT_DIR="$HERMES_HOME/cron/output/<name>"
mkdir -p "$OUT_DIR"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
LOG="$OUT_DIR/${DATE}.log"

{
    echo "=== <name> $DATE ==="
    python3 "$HERMES_HOME/scripts/<target_script>.py" 2>&1
    python3 -c "
import sqlite3, pathlib
db = pathlib.Path('$HERMES_HOME/memory_store.db')
if db.exists():
    conn = sqlite3.connect(db)
    cur = conn.execute('SELECT COUNT(*) FROM facts')
    print(f'fact_store: {cur.fetchone()[0]} 条')
    conn.close()
"
} 2>&1 | tee "$LOG"
echo "[wrapper 完成] → $LOG"
```

**关键要素**：set -e（任一命令失败立即退出）+ { } 2>&1 | tee（同时输出和写文件）+ 健康检查输出。

## Cron Job 配置

### 正确：no_agent=true + script
```
cronjob(update, job_id="<id>", script="<wrapper.sh>", no_agent=True)
```

### 错误：只有 prompt（LLM 会偷懒）
```
cronjob(update, job_id="<id>", prompt="执行 idle_learning 轮次...")
# 缺少 script + no_agent → Hermes 启动 LLM agent
# LLM agent 写报告，不真跑脚本
```

## ABCD 扫描：独立超时模式

```python
import threading, subprocess

def run_with_timeout(fn, timeout=10):
    results = {}
    def target():
        results['v'] = fn()
    t = threading.Thread(target=target)
    t.daemon = True
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        raise TimeoutError(f"超时 {timeout}s")
    return results.get('v')

def run_abcd_scan():
    results = {}
    # A 视觉：ps aux，~1s
    def a_visual():
        r = subprocess.run("ps aux", shell=True, capture_output=True, text=True, timeout=8)
        return {"ok": True, "summary": f"{len(lines)} 进程"}
    # B 论文：缓存+降级，~5s
    # C 安全：后台，~5s（不阻塞）
    # D 执行层：~3s
    # 每步独立超时，互不阻塞
```

## 外部 API 降级策略（以 arXiv 为例）

```python
CACHE = Path.home() / ".hermes" / "cache" / "arxiv_papers.json"
CACHE_TTL = 3600  # 1小时

def fetch_arxiv():
    # 1. 缓存命中
    if CACHE.exists():
        age = time.time() - CACHE.stat().st_mtime
        if age < CACHE_TTL:
            return {"status": "cached", "papers": json.loads(CACHE.read_text())}
    # 2. 实际请求（curl 有超时）
    r = subprocess.run(
        ["curl", "-s", "--max-time", "8", ARXIV_API_URL],
        capture_output=True, text=True, timeout=10
    )
    if r.returncode == 0 and "entry" in r.stdout:
        papers = parse_arxiv(r.stdout)
        CACHE.write_text(json.dumps(papers))
        return {"status": "ok", "papers": papers}
    # 3. 降级：过期缓存
    if CACHE.exists():
        return {"status": "cached_stale", "papers": json.loads(CACHE.read_text())}
    return {"status": "skip"}
```

## 2026-07-09 phantom output 审计参考
详见：`references/phantom-output-audit-20260709.md`

## 本系统已知 Wrapper（截至 2026-07-09）

| Wrapper | 用途 | 验证 |
|---------|------|------|
| morning_briefing.sh | 每日早晨简报（天气+日历+待办） | ✅ 通过 |
| monthly_finance.sh | 每月1日家庭收支汇总 | ✅ 通过 |
| idle_learning_wrapper.sh | ABCD 四方向扫描 | ⚠️ 空转输出，fact_store 本轮无增长 |
| abcd_auto_fix_wrapper.sh | ABCD 缺口修复 | 通过 |
| daily_skill_intake_wrapper.sh | 每日 skill 采集 | 通过 |
| knowledge_miner_wrapper.sh | 知识挖掘 | 通过 |
| auto_skill_scan_wrapper.sh | 失败模式扫描 | ✅ 已修复：去掉 `scan --min-count` 参数，skill 文件正常落地 |
| self_model_update_wrapper.sh | 自我模型更新 | ⚠️ phantom output（auto_skill_count 从内存计，非文件计） |
| session_bootstrap_check.sh | 重启后会话恢复 | 通过 |
| idle_killer.sh | 空闲进程清理 | 通过 |
| idle_lsp_killer.sh | LSP 进程清理 | 通过 |
| memory_watchdog_cron.sh | 内存守护 | 通过 |
| agent_status_broadcast.sh | 状态广播 | 通过 |
| drain_watchdog.sh | 队列守护 | 通过 |
| task_watchdog.sh | 任务守护 | 通过 |

> ⚠️ 标记的 wrapper 需要加落地验证。self_model.json 的 `auto_skill_count` 从内存计数，
> 不等于实际落地文件数，需交叉验证 `~/.hermes/skills/auto-generated/` 是否存在。

## 验证清单

```bash
# 1. wrapper 可执行
chmod +x ~/.hermes/scripts/<wrapper>.sh
bash ~/.hermes/scripts/<wrapper>.sh

# 2. cron job 配置正确（重要：检查 script 字段是纯文件名，no_agent 字段是 true）
cronjob(action=list)  # 检查 script + no_agent 字段

# 3. 手动触发验证
hermes cron run <job-id>
cat ~/.hermes/cron/output/<name>/<date>.log   # 确认输出内容符合预期，不只是 "succeeded"
```


## 2026 更优方案（全网调研 2026-08 迭代）
silentwatch-mcp — https://github.com/temurkhan13/silentwatch-mcp
捕获 cron 的"exit-0 但空输出"静默失败、重试风暴、action-budget 泄漏，比单纯监控退出码更可靠。
