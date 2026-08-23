# 2026-07-11 系统状态快照

## 用户手动变更（未提交 git）

### 核心身份重构
| 文件 | 变更 |
|------|------|
| SOUL.md | 完全重写：从"义乌市迅龙贸易 AI 同事" → "Mac mini 数字人" |
| .skills_prompt_snapshot.json | 重写：从 1688 业务技能 → Hermes 核心技能 |

### 删除的文件
- `.n8n_backup/` — n8n 备份整个目录（Bin 1MB → 0）
- `1688-automation.md` — 1688 自动化文档
- `1688-procurement.md` — 1688 采购文档
- `active-proactive-scan.md` — 主动扫描文档
- `automation/n8n-hermes-integration/` — n8n 集成整个目录
- `audio_cache/*.ogg` — 所有语音缓存文件（~20个）
- `.n8n_backup/config`、`.n8n_backup/database.sqlite`、`.n8n_backup/nodes/package.json`

### 配置修改
- `.env.example` — 移除 `OLLAMA_API_KEY`、`OLLAMA_BASE_URL`
- `agent-tooling/autonomous-ai-agents/references/` — 修改了 perception-kernel.md、turix-cua.md
- `engineering/humanization-engine/SKILL.md` — 新增
- `engineering/resilience-engine/SKILL.md` — 新增

### git 状态
```
git -C ~/.hermes status
On branch master
Changes not staged for commit:
  modified:   SOUL.md
  modified:   .skills_prompt_snapshot.json
  modified:   .env.example
  modified:   .update_check
  deleted:    .n8n_backup/*
  deleted:    1688-*.md
  deleted:    automation/n8n-hermes-integration/*
  deleted:    audio_cache/*.ogg
  modified:   agent-tooling/autonomous-ai-agents/references/*
  modified:   engineering/humanization-engine/SKILL.md
  modified:   engineering/resilience-engine/SKILL.md
```

## 当前活跃进程
- OmniRoute server: PID 95366 (node bin/omniroute.mjs serve)
- Python HTTP server 18999: PID 14009
- Gateway: PID 2225
- Chrome: PID 2539

## 内存大户（2026-07-11 10:23）
1. Hermes gateway python: 687.9MB
2. Clash Mi: 604.1MB
3. Chrome: 492.8MB
4. Claude.app: 340.2MB
5. mediaanalysisd: 289.6MB

## 今日关键事件
- 01:00 — patrol 检测到 Gateway STOPPED，self-heal 恢复
- 01-06 点 — 每日学习 cron 任务运行
- 07:00 — memory_store.db 更新（3.6MB）
- 09:00 — daily_health 检查通过（Gateway 运行中）
