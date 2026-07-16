# Manual Config Audit SOP

用户问"手动改的配置是否都检查到"时的标准流程。

## 触发词
- "手动改的配置"
- "检查配置"
- "我之前改了"
- "配置变更"
- "审计配置"

## 步骤（按序执行）

### 1. 查 git diff（未提交变更）
```bash
git -C ~/.hermes diff --stat 2>/dev/null | head -50
git -C ~/.hermes diff .env.example 2>/dev/null | head -60
```

### 2. 查会话历史（找用户说过的变更）
```
session_search(query="手动更改 配置 修改 SOUL", limit=3, sort="newest")
```

### 3. 验证关键文件（实际状态）
| 文件/目录 | 验证命令 |
|-----------|---------|
| SOUL.md | `cat ~/.hermes/SOUL.md | head -20` |
| skills 目录 | `ls ~/.hermes/skills/` |
| crontab | `crontab -l | grep patrol` |
| scripts | `ls ~/.hermes/scripts/anti_counter_question_scan.py` |
| .env.example | `grep -i ollama ~/.hermes/.env.example` |

### 4. 系统状态（进程验证）
```bash
ps aux | grep hermes | grep -v grep  # Gateway 在跑
pgrep -f hermes-gateway || pgrep -f "hermes_cli.main gateway run"  # 进程检查
```

### 5. 汇报格式
用表格列示每项变更 + 状态（✅已确认/⚠️路径不存在/❌未生效）

## 常见坑

- **QQBot adapter.py 路径不存在**：当前 Hermes 结构已变，`~/.hermes/gateway/platforms/qqbot/adapter.py` 不存在 → QQBot 未安装或已移除
- **pgrep 误判**：需 `ps aux | grep hermes` 双重验证
- **git diff 为空≠没改过**：用户可能已 commit 或文件不在 git 管理下
