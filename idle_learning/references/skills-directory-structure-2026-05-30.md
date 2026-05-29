# Skills 目录结构说明（2026-05-30）

## 发现背景

扫描 `hermes skills list` 发现技能返回"未安装"，但实际已存在于 `~/.hermes/skills/` 目录。原因：Skills 采用 category 子目录结构，list 显示扁平名称但实际路径在各 category 下。

## 验证方法

```bash
# ❌ 错误：直接检查扁平路径
ls ~/.hermes/skills/macos-computer-use/SKILL.md  # → not found

# ✅ 正确：用 find 搜索
find ~/.hermes/skills/ -name "macos-computer-use" -type d
# → /Users/aimac/.hermes/skills/apple/macos-computer-use

# 或检查 category 子目录
ls ~/.hermes/skills/apple/
```

## 技能路径对照（2026-05-30 实测）

| 技能名 | 实际路径 |
|--------|----------|
| macos-computer-use | `~/.hermes/skills/apple/macos-computer-use/` |
| systematic-debugging | `~/.hermes/skills/software-development/systematic-debugging/` |
| jupyter-live-kernel | `~/.hermes/skills/data-science/jupyter-live-kernel/` |
| obsidian | `~/.hermes/skills/note-taking/obsidian/` |
| huggingface-hub | `~/.hermes/skills/mlops/huggingface-hub/` |
| agentmail | `~/.hermes/skills/email/agentmail/` |

## 验证脚本

```bash
# 快速验证技能是否存在
for skill in macos-computer-use systematic-debugging jupyter-live-kernel obsidian huggingface-hub agentmail; do
    found=$(find ~/.hermes/skills/ -name "$skill" -type d 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        echo "✅ $skill → $found"
    else
        echo "❌ $skill not found"
    fi
done
```