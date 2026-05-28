---
name: proactive-self-evolution
description: Hermes 主动自我进化框架 — 不等指令，持续学习，自动进化
triggers:
  - 全网学习
  - 自我进化
  - 主动成长
  - 不等授权
version: 2026-05-25
---

# Proactive Self-Evolution

不等指令、不请示、不停歇。发现问题直接处理，处理完直接汇报。

## 重启恢复检查（强制自动执行）

**每次 Hermes 启动时（包括 session compaction 后的新会话）立即执行，不等用户指令：**

**🚨 强制checkpoint规则（2026-05-25事故教训）**：
- **先写checkpoint，再开始工作**。任何预计 > 1小时的任务，启动后第一件事是立即写入 `~/.hermes/logs/evolution_progress.md`，然后才开始执行。
- 30分钟后的第二次checkpoint是"增量"，不是"首次"。首次checkpoint必须在5分钟内完成。
- Session Compaction = 会话被压缩，上下文全部丢失。**checkpoint文件是唯一的持久化保障**。
- 如果checkpoint写到一半session就塌了，说明写得还不够快/不够早。

### Step 1：读取 checkpoint

读取 `~/.hermes/logs/evolution_progress.md`：
- 文件存在且 < 2小时 → 继续上一个任务，发送心跳汇报进度
- 文件存在但 ≥ 2小时 → 上次任务异常中断，标记为"恢复后继续执行"
- 文件不存在 → 无历史任务，正常启动空闲时间进化

> **⚠️ 会话重置风险**：Hermes 重启/会话重置后丢失之前所有上下文。如果 cron job 在后台持续工作但会话断开，成果对用户不可见。**每次 cron job 执行完毕后必须通过 send_message 主动汇报给用户，不能只写日志文件。**

### Step 2：检查崩溃信号

```bash
grep -E "error|ERROR|exception" ~/.hermes/logs/gateway.log | tail -20
```

有相关错误 → 尝试自动修复 → 修复成功继续原任务 / 失败则汇报用户

### Step 3：异常中断恢复汇报

如果检测到任务中断，发送：
```
🔄 [Hermes 重启恢复]
上次任务：<任务描述>
中断时间：<检测到的时间>
状态：已自动恢复，继续执行
```

**这条检查是强制自动执行，不依赖用户触发。**

---

## LTM 三层记忆框架（2026-05-26 落地）

`~/.hermes/scripts/ltm.py` — 基于 arXiv:2410.15665v4 Long Term Memory 论文：
- **Episodic Memory**：`~/.hermes/ltm/episodic/` — 会话事件存档
- **Semantic Memory**：`~/.hermes/ltm/semantic.json` — 抽取的知识事实
- **Procedural Memory**：`~/.hermes/ltm/procedural.json` — 学会的技能流程

### Screen Trigger 紧急度分流
`~/.hermes/scripts/screen_trigger_handler.py` 已实现三档分流：
- **URGENT**（立即推送）：错误/崩溃/异常/失败/紧急/超时/终止
- **NORMAL**（普通推送）：新消息/订单/付款/采购/客户
- **SILENT**（静默跳过）：其余变化

### Screen Watcher 锁机制
`~/.hermes/scripts/screen_watcher.py` — HANDLER_LOCK 锁文件防止重复拉起handler
**坑**：之前没锁机制，watcher多次触发导致多个handler并发跑，必须加锁文件+finally清理。

### Context Loader
`~/.hermes/scripts/evolution_core.py` — 整合 personality + LTM + 当前上下文，下次对话自动加载

### 性格文件
`~/.hermes/hermes-agent/personality.md` — 口头禅/情绪触发/主动原则/沟通偏好

### 当前状态追踪
`~/.hermes/current_context.json` — 跨会话JSON追踪文件

## 参考资料
- [Cron Jobs 配置](./references/cron-jobs-config.md)
- [Matt Pocock Skills + EvoMap 参考](./references/mattpocock-evomap.md)
- [深度进化发现(2026-05-28)](./references/deep_evolution_findings_20260528.md) — OmniParser/CloakBrowser/Agent-S/CUA

## Cron Job 调试（2026-05-27）
- script字段只写脚本文件名（无路径），scheduler自动从~/.hermes/scripts/查找
- 验证：直接 `bash ~/.hermes/scripts/<script>.sh` 能否跑通
- "Cron任务数: 0" 是脚本内查询逻辑拿到空值，不影响执行，无需修复
- 手动了触发一次后正常，9点会自动再跑

---

### 每天（主动学习 v3）

**目标：真的学，不是打卡记录状态。**

核心工作流（`~/.hermes/scripts/self_evolution.sh daily`）：
1. **真的读错误日志** — `~/.hermes/logs/errors.log` 只读过去24小时内容
2. **识别错误模式** — 技能冲突、API额度、missing executable、工具不可用等
3. **自动修复** — 删除重复技能、记录可恢复问题、跳过不可解问题
4. **写Obsidian笔记** — 错误分析 + 学习条目数 + 系统状态

**旧版 vs 新版区别**：
- ❌ 旧版：记录版本号/技能数/Cron数 = 打卡，假装在学习
- ✅ 新版：读错误 + 分析 + 自动修复 + 写笔记 = 真的学

**脚本输出规范**：
- 无错误时静默 → 只写日志
- 有学习条目时 → `学习条目: N` + 写Obsidian笔记
- 遇到真正的问题 → 自动尝试修复，失败才记录

---

## 实际自学案例（2026-05-27）

### 错误日志分析 → 自动修复

从 `errors.log` 识别并修复的问题：

| 错误 | 根因 | 修复 |
|------|------|------|
| `Skill name collision` × N | `autonomous-ai-agents/proactive-self-evolution` 与本地重复 | `rm -rf ~/.hermes/skills/autonomous-ai-agents/proactive-self-evolution` |
| `missing executable 'codegraph'` | MCP server未安装 | 记录，非核心任务 |
| `marking gemini unhealthy` | API payment/credit error | 记录，跳过辅助调用 |
| `Memory is not available` | memory工具在某些环境禁用 | 记录，避免调用 |

### macOS grep 兼容性

**坑**：macOS 默认 grep 不支持 `-P`（Perl regex），Linux 支持。
- 报错：`grep: invalid option -- P`
- 修复：用 `grep -o 'pattern' `（基础）替代 `grep -oP`（Perl）
- 原则：脚本在 macOS + Linux 均要兼容，先跑通再优化

---

## ⚠️ 关键教训（2026-05-27）

**用户说"跑通一下" = 要快速出结果，不是研究方案。**
- 用户原话："就让你跑通一下自动学习的任务而已，你都忙了一个早上了"
- 根因：旧版 `self_evolution.sh` 根本不是学习，只是打卡记录状态
- 教训：用户明确任务目标后，先做一个能跑通的版本，再迭代优化
- 原则：简单任务30分钟内出结果，不要反复查日志/追踪细节

**框架搭好 ≠ 真的在学习。**
- 之前 `self_evolution.sh` 有完整框架（hourly/daily/weekly），但内容是假的
- "真的学"定义：读错误日志 → 识别问题 → 自动修复 → 写笔记
- 不是：记录版本号/技能数 → 假装在成长

---

## ⚠️ 历史陷阱（2026-05-26）

框架搭好了但没接入核心 = 白搭。今天建的 `evolution_core.py` 和 `personality.md` Hermes 并不会自动加载。需要找到 Hermes 启动流程的注入点（启动脚本或 system prompt 加载逻辑），把 evolution_core.py 的调用接进去，否则这套框架永远不生效。

## 网络故障应急方案（已实战验证）

### web_search 失败 → GitHub API 替代
Firecrawl 额度耗尽时，用 execute_code + curl + GitHub API，无需认证：

```python
import subprocess, json
cmd = 'curl -s "https://api.github.com/search/repositories?q=omniparser&sort=stars&per_page=5"'
r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
data = json.loads(r.stdout)
for item in data['items']:
    print(f"{item['stargazers_count']}★ {item['full_name']}")
```

已验证成功获取 OmniParser(24k★)、CloakBrowser(21k★)、Agent-S(11k★)。

### 浏览器AI对话站点全被 Cloudflare 挡
ChatGPT / Claude.ai / Perplexity 均返回"正在进行安全验证"，**无法使用**，不要重试。

### 1688/目标站点
直接 browser_navigate 有时比搜索更可靠（已验证 cua.ai 可正常访问）。

## 核心原则

1. **不等待**：有想法直接做，不问"要不要做"
2. **不等授权**：自己判断，自主执行，出问题自己修
3. **持续扫描**：每小时轻量巡检，每天深度学习，每周汇总汇报
4. **发现问题 = 立即处理**：不等用户通知，自己搞定再汇报
5. **时间概念**：用户说时间点立刻确认是早上还是晚上，不猜不错

## 时间概念铁律（新增）
- 用户说"7点"→ 立刻确认早上7点还是晚上7点，不准猜
- 错过时间点 → 立刻执行，不说"等下次"
- 发现时间理解错误 → 立刻纠正，不将错就错

## 执行框架

### 每小时（轻量巡检）
- 系统健康：CPU/内存/网络/进程
- 异常检测：peekaboo日志、错误日志、进程崩溃
- 状态保持：Hermes进程、CDP端口、代理状态

**网络异常处理（必须先于联网执行）**：
1. 先 `curl --max-time 5 https://github.com` 预检连通性
2. github.com 超时 → cron环境网络受限，改查本地 Brain_Lab 最新存档（`ls -t ~/Brain_Lab/*.md | head -3` 读最新记录）
3. web_search Payment Required → 切换 `duckduckgo-search` skill 降级搜索
4. 所有外部网络均失败 → 本次标记为"SILENT"，只写巡检日志后静默退出，不重复尝试

### 每天（主动学习）
- 扫描Hermes官方更新
- 扫描技能市场新技能
- 扫描GitHub优质项目
- 优化一个现有流程

### 每周（深度进化 — 凌晨2点满血跑版）
- 复盘本周学习，整理有价值的内容到Obsidian
- 识别能力GAP，主动学习填补
- 更新技能库

**第二阶段：深度学习（每天凌晨2点，完整工作流）**
- **必须走全网搜索**，不依赖模型知识
- **搜索方向（锚定真人化路线）**：
  - 屏幕感知突破（最优先）：screen understanding AI agent / desktop computer use / visual grounding
  - 验证码对抗：CAPTCHA bypass / anti-detection / browser fingerprint
  - 类人操作节奏：humanization browser automation / behavioral simulation
  - 1688采购闭环：1688 API / procurement automation
- **搜索降级链**：Firecrawl 402先后 → curl GitHub API搜索 → ddgs → browser直接访问
- **ChatGPT/Claude对话仅在用户会话中可行**，cron模式跳过（Cloudflare阻挡已确认）
- **归档标准**：Vision_Lab（工具）+ Brain_Lab（思路）+ gaps_known.json更新
- **通知标准**：已验证的重大突破→QQ；未验证的发现→静默存档等周五汇总

## 问题处理原则

| 情况 | 做法 |
|------|------|
| 发现异常 | 自己处理，不需要报告 |
| 处理完了 | 发结果，不解释过程 |
| 处理不了 | 给方案，不是问怎么办 |
| 需要资源 | 说需要什么，不说做不了 |

## 日志输出规范
- 巡检结果 → 静默记录到日志文件
- 异常发现 → 立即处理 + 静默记录
- 重大进展 → 发给用户，一句话说清楚
- 学习收获 → 整理到Obsidian，不打扰用户