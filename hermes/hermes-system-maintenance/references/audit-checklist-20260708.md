# Hermes 系统审计检查清单

来源：2026-07-08 手动审计，清理其他AI留下的混乱。

## 审计顺序（推荐）

```
1. hermes config check        # 快速扫描配置问题
2. ~/.hermes/SOUL.md          # 内容重复/过时skill引用/大小检查
3. ~/.hermes/AGENTS.md        # 内容重复检查
4. ~/.hermes/memories/MEMORY.md  # 技术记忆，过期/重复
5. ls ~/.hermes/skills/       # symlink检查 + 数量统计
6. cronjob list               # 禁用但残留的job
7. find ~/.hermes/cron/output -name "*.md" -size +50k  # 大输出文件
8. ls ~/.hermes/scripts/       # 孤立/废弃脚本
```

## 本次审计发现的问题

| 问题 | 修复命令 | 状态 |
|------|---------|------|
| 17个 dead symlinks（skills/根目录） | `find ~/.hermes/skills -maxdepth 1 -type l -exec sh -c '[[ ! -e "$(readlink "$1")" ]] && rm "$1"' _ {} \;` | ✅ 已清理 |
| 1个 dead symlink（.archive/ai-radar） | `rm ~/.hermes/skills/.archive/ai-radar` | ✅ 已清理 |
| SOUL.md skill引用错误（hermes-vision-agent等不存在） | patch SOUL.md | ✅ 已修复 |
| 禁用cron job大输出文件（每日skill采集） | `rm ~/.hermes/cron/output/4862dc17ff7e/*.md` | ✅ 已清理 |
| SOUL.md内容与AGENTS.md重复 | 需手动合并 | ⏳ 待处理 |
| skills/目录过大（symlink占位） | 已清理 | ✅ |

## SOUL.md vs AGENTS.md 职责划分

- **SOUL.md**：身份定位 + 数字人宣言 + 工具栈现状 + 主宰边界 + 进化阶段
- **AGENTS.md**：行为准则 + 工作流规则 + 铁律 + 触发词 + 复盘机制
- **重叠危害**：AI读取两份文件时内容打架，同一规则出现多次导致困惑

## Symlink 清理标准命令

```bash
# 一键清理所有 dead symlinks（两级深度）
find ~/.hermes/skills -maxdepth 2 -type l 2>&1 | while read l; do
  t=$(readlink "$l")
  if [[ ! -e "$t" ]]; then
    echo "CLEAN: $l"
    rm "$l"
  fi
done
```
