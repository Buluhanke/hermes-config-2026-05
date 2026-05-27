# self_evolution.sh 设计文档

## 版本历史

| 版本 | 日期 | 变化 |
|------|------|------|
| v1 | 2026-05-25 | 检查点监控，记录Hermes版本/技能数/Cron数 |
| v2 | 2026-05-26 | 加入从错误日志提取信息 |
| v3 | 2026-05-27 | 真正学习：读errors.log + 自动修复技能冲突 + 写Obsidian笔记 |

## v3 核心逻辑

```bash
# daily 模式
1. 检查 Hermes 是否在运行
2. 检查 CDP 9333 端口
3. 检查代理 7897
4. 读 errors.log 过去24小时
5. 匹配错误模式（grep -o 兼容macOS）
6. 自动修复技能冲突（检查重复skill目录并删除）
7. 写 Obsidian 学习笔记到 ~/Obsidian/迅龙贸易/AI进化/
8. 输出 "每日学习完成，学习条目: N"
```

## 错误模式匹配

```bash
# 兼容 macOS 的 grep（不用 -P）
SKILL_CONFLICT=$(grep -l "Skill name collision" $LOG_FILE 2>/dev/null | wc -l | tr -d ' ')
```

## Obsidian 笔记路径

```
~/Obs龙贸易/AI进化/YYYY-MM-DD-每日学习.md
```

笔记结构：
- 系统状态
- 错误分析
- 发现的问题
- 技能统计
- 学习条目

## Cron Job 配置

```bash
# 正确写法
cronjob create \
  --prompt "bash ~/.hermes/scripts/self_evolution.sh daily" \
  --schedule "0 9 * * *" \
  --name "Hermes每日学习"
```

## 坑

1. **macOS grep -P 不支持**：用 `grep -o` + `grep` 组合替代
2. **cron 环境无 HOME**：`bash ~/.hermes/scripts/...` 要写绝对路径
3. **脚本路径**：cron job 的 script 字段只写文件名，scheduler 自动找 ~/.hermes/scripts/
