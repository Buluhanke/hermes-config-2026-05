# 技能注册表 & 跨平台协调工具（2026-06-07）

## 背景

三个聊天平台（QQ/微信/Telegram）共享同一套 `~/.hermes/skills/`，技能天然互通。但跨平台协调需要两个工具：
1. **技能注册表** — 扫描所有嵌套 skill，生成中央索引
2. **跨平台状态同步** — 各 agent 广播自身状态，共享知识

## 工具清单

### skill_registry.py
路径：`~/.hermes/scripts/skill_registry.py`
功能：递归扫描所有嵌套 SKILL.md，生成中央注册表
```bash
python3 ~/.hermes/scripts/skill_registry.py list              # 列出所有 skill（含嵌套）
python3 ~/.hermes/scripts/skill_registry.py find "关键词"     # 搜索 skill
python3 ~/.hermes/scripts/skill_registry.py show <name>      # 查看单个 skill 详情
python3 ~/.hermes/scripts/skill_registry.py refresh           # 重新扫描生成
python3 ~/.hermes/scripts/skill_registry.py count             # 统计 skill 总数
```
输出：`~/.hermes/.skill_registry.json`（190+ 个 skill，含 name/description/triggers/path）

### agent_status.py
路径：`~/.hermes/scripts/agent_status.py`
功能：跨平台 agent 状态广播 + 技能摘要 + 共享知识库
```bash
python3 ~/.hermes/scripts/agent_status.py whoami            # 查看当前 agent 身份
python3 ~/.hermes/scripts/agent_status.py list              # 查看所有在线 agent
python3 ~/.hermes/scripts/agent_status.py announce "消息"  # 广播状态
python3 ~/.hermes/scripts/agent_status.py skill_summary    # 生成技能摘要
python3 ~/.hermes/scripts/agent_status.py learn "知识"    # 写入共享知识库
python3 ~/.hermes/scripts/agent_status.py query "关键词"   # 查询共享知识库
```
状态文件：`~/.hermes/.agent_status.json`
共享知识库：`~/.hermes/.shared_knowledge.md`

## 架构说明

```
各平台 Agent（Telegram/QQ/WeChat）
         ↓ 调用
  skill_registry.py ←→ ~/.hermes/.skill_registry.json
  agent_status.py  ←→ ~/.hermes/.agent_status.json
                   ←→ ~/.hermes/.shared_knowledge.md
         ↓ 共用
    ~/.hermes/skills/（技能天然共享）
```

**重要限制**：三个平台的 session 独立——技能互通，但对话历史不相通。

## 已知的拢

### 1. whoami 返回 unknown
`agent_status.py whoami` 返回 `Agent ID: unknown / Platform: unknown` 是正常的——脚本需要接入各平台 adapter 才能读取真实身份。当前版本 v1.0 还没有平台感知能力。
**何时修**：当需要把 agent_status.py 接入 cron job 或自动化流程时再扩展。

### 2. 技能描述为空
部分 skill 的 SKILL.md 没有 frontmatter `description` 字段，导致注册表里描述为空。不影响功能，只是索引质量略低。

### 3. Telegram adapter 集成方式
要让我每次启动时自动执行 `agent_status.py announce`，需要通过 Hermes cron job 实现：
```bash
# 每15分钟刷新一次注册表 + 广播状态
cronjob(action='create', name='skill-registry-refresh',
  prompt='python3 ~/.hermes/scripts/skill_registry.py refresh && python3 ~/.hermes/scripts/agent_status.py announce',
  schedule='*/15 * * * *')
```
