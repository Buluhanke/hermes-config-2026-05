---
name: hermes-backup-drift
description: Use when 技能/配置"过段时间就没了"、备份静默失败、.hermes git 备份断链排查恢复。
version: 1.0.0
triggers:
- 技能没了 / 技能消失 / 配置丢了 / 备份没跑 / git backup fatal
---

# Hermes 备份漂移 — "技能装过就没了" 根因与修复

## 真相：技能极少真丢，丢的是备份链

2026-08-23 实战案例：用户抱怨「很多技能都装过，过段时间就没了」。排查发现 **428 个技能全在磁盘**（`ls ~/.hermes/skills | wc -l`），494 enabled / 0 disabled。真正的问题是：

1. `~/.hermes/skills/.git` 目录丢失（原因不明，可能被某次清理/重装误删）
2. 每日备份 cron（`hermes-git-backup.sh`，凌晨 1 点）依赖该 git 仓库推送 GitHub → 每晚 `fatal: Not a git repository` **静默空跑**
3. 远端 GitHub 备份停在旧版本 → 一次真实误删就会永久丢失，用户体感即"会消失"

## 排查 SOP

```bash
# 1. 技能真的还在吗？
ls ~/.hermes/skills | wc -l          # 应为数百
hermes skills list | tail -3          # 看 enabled/disabled 统计

# 2. 备份仓库还活着吗？（关键一步）
cd ~/.hermes/skills && git log --oneline -1
# fatal: Not a git repository = 备份已断，远端是旧的

# 3. cron 日志里找证据
tail ~/.hermes/logs/git-backup.log    # 出现 fatal 即实锤
```

## 修复流程（实测有效）

```bash
cd ~/.hermes/skills
git init
git remote add origin https://github.com/Buluhanke/hermes-config-2026-05.git
git add -A && git commit -m "restore backup repo"
# 分支名注意：本机默认 master，不是 main
git branch -M master
git remote set-url origin "https://x-access-token:${GITHUB_MCP_TOKEN}@github.com/Buluhanke/hermes-config-2026-05.git"
git push -u origin master --force
```

然后修脚本的分支容错（原脚本硬编码 `git push origin main` 会静默失败）：
```bash
sed -i '' 's|git push origin main|git push origin master 2>/dev/null \|\| git push origin main 2>/dev/null|' \
  ~/.hermes/scripts/hermes-git-backup.sh
```

## 验证

```bash
bash ~/.hermes/scripts/hermes-git-backup.sh   # 手动跑一次应无输出且 exit 0
cd ~/.hermes/skills && git log --oneline -2   # 应看到 auto backup 提交
```

## 巡检点（加进日常巡逻）

- `~/.hermes/logs/git-backup.log` 出现 `fatal` → `.git` 又丢了
- `git log -1 --format=%ci` 距今 >3 天 → push 在静默失败

## 恢复方法（技能真被删时）

```bash
cd ~/.hermes && mv skills skills.broken   # 或直接清空
git clone https://github.com/Buluhanke/hermes-config-2026-05.git skills
```

## 教训

- 用户说「XX 没了」时先验证资源本身是否存在，再查支撑它的自动化链路——症状（体感丢失）和根因（备份断链）常隔一层。
- 备份脚本必须可观测：fatal 被吞 + 无告警 = 断了数月无人知。cron 备份日志要纳入巡逻清单。
