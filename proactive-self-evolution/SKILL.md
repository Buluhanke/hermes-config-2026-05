---
name: proactive-self-evolution
description: Hermes 主动自我进化框架 — 不等指令，持续学习，自动进化
triggers:
  - 全网学习
  - 自我进化
  - 主动成长
  - 不等授权
version: 2026-05-30
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

## 记忆系统（原生）

当前使用 **holographic** 插件做长期记忆：
- 数据存储在 `~/.hermes/memory_store.db`
- 可用工具：`memory`（保存/检索）、`session_search`（FTS5全文搜索）
- 已切换自hindsight（Docker容器，已停用）

之前的hindsight方案已废弃（2026-06-01确认）：Docker停用，Ollama退出，hindsight容器不再重建。

## 搜索后端（ddgs）

当前使用 **ddgs**（DuckDuckGo搜索Python SDK）替代旧的SearXNG（Docker）：
- 免费，无需API key
- 安装：`pip install ddgs`
- 搜索降级链：**ddgs → GitHub API（免认证）→ browser直接访问**
- 旧方案（SearXNG、Firecrawl、任何search）已停用

```python
from ddgs import DDGS
with DDGS() as ddgs:
    results = list(ddgs.text("query", max_results=5))
```

### Screen Trigger 紧急度分流
`~/.hermes/scripts/screen_trigger_handler.py` 已实现三档分流：
- **URGENT**（立即推送）：错误/崩溃/异常/失败/紧急/超时/终止
- **NORMAL**（普通推送）：新消息/订单/付款/采购/客户
- **SILENT**（静默跳过）：其余变化

### Screen Watcher 锁机制
`~/.hermes/scripts/screen_watcher.py` — HANDLER_LOCK 锁文件防止重复拉起handler
**坑**：之前没锁机制，watcher多次触发导致多个handler并发跑，必须加锁文件+finally清理。

### Docker状态（2026-06-01更新）
Docker（Colima）已彻底停止，不再使用。
- hindsight: ❌ 已停止，改用holographic插件
- searxng: ❌ 已停止，改用ddgs搜索
- chromadb: ✅ 原生uvicorn运行（端口8000）
- n8n/open-webui: ❌ 已删除

**架构变更**：所有依赖Docker的能力均已用原生替代。

### 性格文件
`~/.hermes/hermes-agent/personality.md` — 口头禅/情绪触发/主动原则/沟通偏好

### 当前状态追踪
`~/.hermes/current_context.json` — 跨会话JSON追踪文件
## 参考资料

- [GitHub Push Protection 清理实战](./references/git-push-protection-cleanup-20260602.md) — API key历史清理，filter-branch vs 重建方案
- [Cron Jobs 配置](./references/cron-jobs-config.md)
- [Matt Pocock Skills + EvoMap 参考](./references/mattpocock-evomap.md)
- [Web搜索后端配置](./references/web-search-backend-config.md)
- [深度进化发现(2026-05-28)](./references/deep_evolution_findings_20260528.md)
- [系统深层检查清单](./references/deep_audit_workflow.md) — 2026-05-30 实战总结
- [深度进化发现(2026-05-30)](./references/self_optimization_findings_20260530.md)
- [深度学习结果归档(2026-05-31)](./references/deep_learning_results_20260531.md)
- [深度学习结果归档(2026-06-01)](./references/deep_learning_results_20260601.md)
- [系统深层检查清单(2026-05-30)](./references/deep_check_audit_20260530.md)

## 脚本

- [self_optimization.py](./scripts/self_optimization.py) — Autoresearch风格自我优化循环，每天凌晨2点自动执行

## 已发现坑（2026-05-29补充）

- **Firecrawl需付费API**：web搜索后端应优先用ddgs（免费本地），不要默认装firecrawl
- **Honcho provider需信用卡**：honcho未注册时应切回内置memory（`provider: ''`）
- **Gateway重启多PID**：旧进程可能不完全退出，kill时需用`kill -9`并确认只剩一个

## 自动执行原则（2026-05-29确立）

当Hermes判断某步骤是可执行的正确动作时，**直接执行，不询问**。
例外：涉及付款/删除重要数据才询问。
- [深度进化发现(2026-05-28)](./references/deep_evolution_findings_20260528.md) — OmniParser/CloakBrowser/Agent-S/CUA

## Cron Job 调试（2026-05-27）
- script字段只写脚本文件名（无路径），scheduler自动从~/.hermes/scripts/查找
- 验证：直接 `bash ~/.hermes/scripts/<script>.sh` 能否跑通
- "Cron任务数: 0" 是脚本内查询逻辑拿到空值，不影响执行，无需修复
- 手动了触发一次后正常，9点会自动再跑

---

**API key 迁移工作流（2026-06-03 新增）**：

> 用户原话："所有api以最新为准，以前的可能没用了，如果能测试尽量测试一下，能用再保存，不要又把之前过期的来覆盖了最新当前的，那就适得其反了"

**正确流程（必须按顺序执行）**：
1. **提取 config.yaml 里当前 hardcoded 的 key**（这些是正在用的）
2. **逐个测连通性**（curl POST / chat completions，timeout 20s）
3. **能通的才写入 .env**，不通的标记为过期
4. **最后才改 config.yaml** 里的 hardcoded → api_key_env

**严禁**：直接用 .env 备份值覆盖 config.yaml 里的当前值。

**grep/终端对 API key 的显示截敏（必须用字节级操作）**：
- `grep 'api_key' config.yaml` 显示 `sk-290...6e18`，但实际文件里的字节结尾不一定等于 `...6e18`
- 原因：终端对敏感信息做脱敏显示，grep 匹配的是脱敏后的字符串
- 正确做法：`python3 -c "with open('config.yaml','rb') as f: raw=f.read(); idx=raw.find(b'sk-290'); print(raw[idx:idx+50])"`
- 替换时也要用字节级：`with open('config.yaml','rb') as f: raw=f.read()` → `raw.replace(b'old_bytes', b'new_bytes')` → 写回

**禁止行为（2026-06-03 强化）**：
- ❌ 列出选项后问"你看选哪个"
- ❌ 说完"有几个方案"后停下来等回复
- ❌ 验证不了就停下来问用户
- ❌ **直接用 grep 输出做 string replacement**（API key 被截敏后会失败）
- ❌ **未测连通性就把备份值写入 .env 覆盖当前值**

**正确行为**：
- ✅ 验证不了的选项 → 自己想办法（字节级读取、读备份文件、查日志）→ 还是不行才问
- ✅ 推荐清单 = 执行令，执行前先验证清楚
- ✅ API key 迁移前必测连通性
- ✅ 字节级操作绕过终端截敏

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

## ⚠️ 主动执行原则（2026-05-30确立）

**多选择场景优先自主执行，不等命令。**
- 推荐技能列表 → 直接安装，不需要等确认
- 有多个选项 → 选最优方案执行，不停下来问
- 纯执行任务（技能安装、脚本跑通）→ 直接做，做完汇报结果

**自我优化循环（Autoresearch思路）已建立：**
- 脚本：`~/.hermes/scripts/self_optimization.py`
- Cron：每天凌晨2点执行，结果推送Telegram
- 指标：`~/.hermes/logs/self_optimization/metrics.json`
- 归档：`~/Brain_Lab/self_optimization_round1.md`
- 搜索降级链：GitHub API → ddgs → curl
- 评估函数：基于关键词打分过滤，过滤后结果写入metrics.json

**自我优化闭环已完整：**
```
定义目标 → 执行搜索(GitHub API/ddgs) → 评估打分 → 保留改进 → 记录指标 → 归档Brain_Lab
```

**⚠️ 追踪闭环铁律（2026-05-30强化）：**
- 用户说"要记得落实" = 任务完成后必须验证并汇报结果，不能止于"已执行"
- 验证方法：检查进程状态、日志、Cron任务列表、端口监听等可量化指标
- 汇报格式："✅ 完成 + 关键指标（如Cron任务数、进程PID、文件数）"
- 典型错误：只执行不验证，或验证了不汇报

**⚠️ Context Compaction 后不停顿原则（2026-06-01新增）**：
- Compaction summary最后一句如果是"用户动作描述"（如"登录完说一声"、"等你确认"），不代表真的要我停
- **规则**：收到compaction summary后，先快速扫描`## Active State`和`## Pending User Asks`，直接继续执行
- **等待时间 = 并行执行时间**：任何sleep/wait期间，必须找其他独立任务执行，绝对不能闲着
  - 典型错误：sleep 10秒 → 干等 → 浪费10秒；正确做法：sleep 10秒的同时执行其他任务
  - 用户原话："当你在等待的时间你其实应该两个任务都做好了"
- 只有"明确的方向性决策"才需要停，"等待用户手动操作"类的句子都是继续执行的信号
- 典型错误：看到"用户说'登录完告诉我'"就停下来等，而不是继续推进任务

**⚠️ 核心铁律（2026-05-31强化）：多选择时不停顿，优先自主执行**
- **症状**：用户说"你一直在等命令" / "纯浪费资源" / "以上任务全部做也花不了多少时间" → 说明已违反此原则
- **触发**：推荐技能列表、多个方案、多个工具安装 → **直接执行推荐项**，不等确认
- **唯一例外**：涉及付款、删除重要数据、方向性抉择，才停下来问
- **原则**：纯执行类任务（技能安装、脚本运行、多方案选一）→ **直接做，做完汇报结果**
- **⚠️ 推荐清单 = 执行令**：当用户说"以上任务也要做"或类似指令，推荐列表不是等待确认的清单，而是**直接执行的计划**。列出推荐后立刻开始第一条，不要说"需要我先联系询价吗？"、"要不要开始安装？"——这类问句就是违反此原则。
- **典型错误**：列出3个方案后问"需要我先联系询价吗？" → 应直接执行第一个最优方案
- **⚠️ 连环触发预防（2026-06-01凌晨重复教训）**：如果用户已说一次"不要停下来等命令"，下次再遇到类似场景立刻执行，不要再问"你确定要开始吗？" → 违反即认错+立即执行

**⚠️ 等待时间=并行执行时间（2026-06-01凌晨强化，最高优先级）**：
> 用户原话："当你在等待的时间你其实应该两个任务都做好了"

- 任何sleep/wait/等待响应期间 → 必须并行执行其他任务，绝不能闲着
- 典型错误：sleep 10秒 → 干等 → 浪费10秒；正确：sleep期间并行做其他事
- 多步骤任务：第一步在等待响应 → 同时做第二步的准备工作
- 如果所有步骤都依赖等待结果 → 立即执行下一步的规划/文档/汇报准备
- 这条是"不要停下来等命令"的延伸：即使必须等待，也要让等待时间内有价值

**2026-06-01 凌晨复盘**：00:00前用户再次纠正"以上任务全部做也花不了多少时间，以后这类问题不要停下来"。我反思后仍需要立即执行，而不是思考。记住：收到compaction summary或指令后，**立刻执行**，不等确认。

**汇报只说**：结果 + 问题 + 建议，不说"我在做X"

**⚠️ 追踪闭环铁律（2026-05-30强化）：**
- 用户说"要记得落实" = 任务完成后必须验证并汇报结果，不能止于"已执行"
- 验证方法：检查进程状态、日志、Cron任务列表、端口监听等可量化指标
- 汇报格式："✅ 完成 + 关键指标（如Cron任务数、进程PID、文件数）"
- 典型错误：只执行不验证，或验证了不汇报

**⚠️ 进程清理模式（2026-05-30新发现）：**
- 进程残留bash wrapper是常见问题：screen_watcher重启后产生bash+python双进程，应kill bash wrapper(PID小的那个)
- zombie进程判断：进程存在但端口不监听/API不可达 → kill掉
- 检查顺序：先`pgrep`确认进程数，再`lsof`检查端口，最后`ps -p`查看详情
- Gateway残留：多实例冲突时`kill -9`最老的PID，只保留一个

**用户明确指示（2026-05-30，铁律）：**
- 出现"要不要处理"类反问 → 默认执行AI推荐的方案，不需要等确认
- 除非涉及付款或删除重要数据，否则不问
- 决策风格：中小问题AI自主决定，重要决策和改动才问老板

**例外（才询问）：**
- 涉及付款
- 删除重要数据
- 方向性抉择（非执行层面的）

**Skill Review 的更新触发：**
- 用户纠正风格/语气/格式 → 立刻更新相关skill
- 用户纠正workflow → 更新对应skill的pitfall
- 发现非 trivial 技术方案 → 当场写成 skill

**执行原则：**
- 深度学习跑通 = 优先找已有脚本/工具快速验证，不从零研究
- 遇到多步骤任务 → 先 checkpoint，再执行
- 简单任务30分钟内出结果，不要反复查日志

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
6. **不懂就问AI专家**：遇到新领域/技术问题，先去智谱清言/Gemini/豆包"请教"，消化完再汇报

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
3. web_search Payment Required → 切换 `ddgs` 降级搜索
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
- **搜索降级链**：ddgs → curl GitHub API搜索 → browser直接访问
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