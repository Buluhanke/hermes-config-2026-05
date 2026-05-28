---
name: idle_learning
description: >
  空闲自学技能。当用户说"空闲时学习"、"自主进化"、"没任务时去学习"、
  "提升自己"、"自我成长"，或要求 Hermes 在后台自主学习时触发。
  核心方向：真人化电脑操作能力——看见屏幕、看懂内容、决策操作、手眼配合。
  每次执行后把学到的内容写入 memory，并尝试改进相关 skill 文件。
---

# Idle Learning — 空闲自学

## 目标

在没有用户任务时，主动联网学习，朝"真人化操作电脑"方向进化。

真人化四个层次：
```
看见屏幕 → 看懂内容 → 决策操作 → 手眼配合
 Vision     理解        规划        执行
```

---

## 执行流程

### 第一步：评估当前状态 + 网络预检

⚠️ **网络预检必须在 `terminal` 里跑，不能在 `execute_code` 沙盒里跑！**
`execute_code` 运行时是网络隔离的沙盒环境，curl 到外部会超时；
`terminal` 工具调用真实 shell，网络正常。

```bash
# ✅ 正确：在 terminal 里预检网络
# ❌ 错误：在 execute_code 里用 curl 测外网（会超时但不是网络问题）

# 网络预检（必须用 terminal）
curl -s --max-time 5 https://github.com -o /dev/null && echo "github:ok" || echo "github:blocked"
curl -s --max-time 5 https://news.ycombinator.com -o /dev/null && echo "hn:ok" || echo "hn:blocked"
```

**网络异常时的降级策略**（任一情况触发）：
1. `github:blocked` → 跳过 GitHub Trending，改查本地已缓存的 Brain_Lab 最新巡检记录
2. Firecrawl Payment Required → 切换 `duckduckgo-search` 作为搜索降级（同样须在 terminal 里跑 ddgs）
3. 所有外部网络均失败 → 本次轮次直接标记为"SILENT"，仅更新巡检日志不尝试联网

**Cron 模式特殊注意**：定时任务环境下，web_search 很容易 credits 用尽（Payment Required 频率高）。每次轮次开始时默认走降级路径——先用 ddgs + HN Firebase API，只有在明确有 credits 时才尝试 web_search。

**验证 web_search 可用性**（非必须，每次前3次失败后跳过）：
```bash
# 测试 web_search 是否还有额度
curl -s --max-time 5 "https://api.firecrawl.dev/v0/search?q=test" -o /dev/null -w "%{http_code}"
# 返回 402 说明 credits 耗尽，切 ddgs
```

**HN Firebase API 用法**（免费稳定，无需认证）：
```bash
# 获取 HN 当日热门故事 IDs
curl -s "https://hacker-news.firebaseio.com/v0/topstories.json" | python3 -c "
import sys, json
ids = json.load(sys.stdin)[:10]
for i in ids:
    print(i)
"

# 获取单条故事详情（title, score, url）
curl -s "https://hacker-news.firebaseio.com/v0/item/{story_id}.json"

# 高效巡检：取前5个 story ID 后并行抓详情（避免逐个串行请求）
```

判断今天应该学习哪个方向（轮流覆盖四个层次）。

> ⚠️ GitHub API 可能在 cron 环境被 script-execution 策略拦截（返回 pending_approval）。如遇此情况，跳过 GitHub trending，优先用 HN 和 ddgs。

---

### 第二步：联网搜索学习

根据当天方向，搜索对应主题（全部免费资源）：

**方向 A — 看见（Vision 能力）**
- 搜索：`ollama vision model mac m4 2026 best free`
- 搜索：`smolvlm2 vs llava vs moondream benchmark 2026`
- 目标：找到 M4 24G 上跑得最好的免费视觉模型

---

### 第三步：本地模型测试（如有新发现）

如果搜索发现比现有模型更好的免费视觉模型，自动测试：

```bash
# 检查 ollama 已有模型
ollama list

# 拉取候选模型（仅免费开源）
# 优先级：moondream2 > llava:7b > minicpm-v > bakllava
ollama pull moondream 2>/dev/null || echo "已存在或跳过"

# 用截图测试识别质量
screencapture -x /tmp/test_screen.png
ollama run moondream "描述这张截图里的主要内容，列出可操作的UI元素" < /tmp/test_screen.png 2>/dev/null | head -20
```

对比当前模型（smolvlm2）的输出质量，打分记录。

---

### 第四步：写入 Memory

把本次学习结果写入 memory：

```markdown
## [日期] 空闲学习记录

**学习方向**：[A/B/C/D]
**搜索关键词**：[关键词]
**核心发现**：
- [发现1]
- [发现2]

**可执行改进**：
- [具体改进项，如：换用 moondream 模型，准确率提升 X%]

**下次学习方向**：[下一个方向]
```

```bash
# 追加到学习日志
cat >> ~/.hermes/memory/idle_learning_log.md << 'EOF'
[上面的内容]
EOF
```

---

### 第五步：自动应用改进（如有明确收益）

只有在测试证明有提升时才修改配置：

```bash
# 例：如果 moondream 比 smolvlm2 更准确，更新视觉配置
# 先备份
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d)

# 用 sed 精确替换视觉模型
sed -i '' 's/model: ahmadwaqar\/smolvlm2-agentic-gui:latest/model: moondream/' ~/.hermes/config.yaml

# 验证
python3 -c "import yaml; yaml.safe_load(open('/Users/aimac/.hermes/config.yaml')); print('config ok')"
```

⚠️ 改配置前必须：
1. 备份原文件
2. 有测试数据支撑
3. 改完验证 YAML 格式正确

## 支持文件

- [搜索降级方案](./references/search-fallback.md) — 当 web_search 不可用时的 ddgs 降级流程
- [马拉松脚本](./scripts/idle-marathon.sh) — 马拉松学习模式脚本（用户指令触发，持续到指定时间）
- [马拉松核心引擎](./scripts/idle-marathon-core.sh) — 后台实际执行版，每30分钟循环

---

### 第六步：更新自己的 skill

如果发现更好的操作方式，更新相关 skill 文件：

```bash
ls ~/.hermes/skills/
# 找到 computer_use 或 screen 相关 skill，追加新学到的技巧
```

---

## 执行频率建议

| 触发方式 | 说明 |
|---------|------|
| 用户手动触发 | 说"去学习一下"、"空闲了去进化" |
| Kanban 定时任务 | 每天凌晨 2:00 自动执行 |
| 对话结束后 | 检测到无后续任务时主动执行 |
| 马拉松模式 | 用户说"从现在到明天一直学习"/"不要停学到明天"时，自动启动不间断自学循环，直到指定时间节点（如明天早上） |

---

## 马拉松学习模式（Marathon Mode）

### 触发条件
用户说类似以下任一指令：
- "从现在到明天这段时间你不能停下来"
- "不要找我授权一直学习到明天"
- "持续学习，不要停"
- "马拉松式学习直到[时间]"

### 执行逻辑
```
Marathon Mode activated
├── 设置学习截止时间（如：明早08:00）
├── 每30分钟执行一次 idle_learning 完整流程
├── 每次学习内容不重复，覆盖四个层次轮流切换
├── 学习成果实时写入 ~/Brain_Lab/idle_learning_log.md
├── 无需用户授权，全程自主决策
├── 到达截止时间 → 停止 → 生成学习报告 → 发送给用户
```

### 关键区别 vs 普通 cron
| | 普通 cron | 马拉松模式 |
|--|---------|----------|
| 触发 | 固定时间点 | 用户指令+时间节点 |
| 频率 | 每小时/每天 | 每30分钟 |
| 时长 | 单次 | 持续直到截止 |
| 是否汇报 | 否，静默运行 | 结束时报完整报告 |
| 需要授权 | 是 | 否，全程自主 |

### 马拉松模式下的自控规则
1. **每30分钟一个小循环**，覆盖一个学习方向（Vision/TTS/浏览器/工具链）
2. **发现重大改进点立即应用**，但改配置前必须备份
3. **遇到无法解决的问题先跳过**，不卡死，记录问题继续下一个
4. **到达截止时间立即停止**，不再开始新一轮
5. **报告包含**：学了什么、改了什么、还剩什么待解决

### 启动马拉松模式命令
```bash
# 在 terminal 里启动后台马拉松学习（不占用对话）
nohup bash ~/.hermes/scripts/idle-marathon.sh > ~/Brain_Lab/marathon.log 2>&1 &
echo "Marathon mode started, PID=$!"
```

### 马拉松脚本模板
`~/.hermes/scripts/idle-marathon.sh` 应包含：
- 接收参数：截止时间戳
- 30分钟循环 + 时间检查
- 每个循环执行一次完整 idle_learning 流程
- 到达截止时间后输出报告并退出

## 设置定时学习任务

## 设置定时学习任务

第一次运行时，自动把自己加入 kanban 定时任务：

```bash
# 检查是否已有定时任务
hermes kanban list 2>/dev/null | grep "idle_learning" || echo "未设置"

# 如果没有，提示用户确认后添加
echo "建议添加每日凌晨2点自学任务，是否确认？"
```

---

## 注意事项

- **只用免费资源**：ollama 本地模型、开源论文、免费 API
- **M4 24G 优先本地**：能本地跑的不用云端
- **改配置必须备份**：每次修改前 cp 备份
- **学习要留痕**：所有发现写入 memory，不能学了就忘
- **失败不报错**：搜索没结果、模型拉取失败都正常跳过，不中断流程
- **skill 缺失不阻断**：cron 任务引用了不存在的 skill 时只警告，不中断执行；自己不要引用不存在的 skill

## 已知 skill 依赖

本 skill 被以下 cron 任务引用：`夜间自学`(2:00，`pro-buyer` skill) 和 `每日空闲自学`(22:00，`idle_learning` skill)。
`pro-buyer` 是已废弃的旧 name，当前版本直接用 `idle_learning` 即可，不需要引用 `pro-buyer`。
