# Skills 重组标准工作流

## 触发场景

用户要求「检查整理 skill 库」「确保所有技能在根目录 depth=1」「删除重复」时执行。

## 工作流（禁止跳过步骤）

### 步骤 0：诊断真实状态（只用 terminal）

**禁止用 execute_code 做文件系统操作。**

```bash
# 枚举所有 SKILL.md 的真实深度
find ~/.hermes/skills -name "SKILL.md" | \
  awk -F'/' '{n=NF-1; print n" "$0}' | \
  sort -n | awk '{print "depth="$1": "$NF}'

# 统计
find ~/.hermes/skills -maxdepth 1 -type d | grep -v 'skills$' | wc -l   # 根目录技能总数
find ~/.hermes/skills -maxdepth 1 -type d -exec test -f {}/SKILL.md \; -print | wc -l  # 含 SKILL.md 数
find ~/.hermes/skills -maxdepth 1 -type d -empty | wc -l              # category 空壳
find ~/.hermes/skills -name "SKILL.md" | awk -F'/' '{if(NF-1>7) print}' | wc -l  # 深层嵌套

# 列出 category 目录及其内容
for d in ~/.hermes/skills/*/; do
  name=$(basename "$d")
  contents=$(ls "$d" 2>/dev/null)
  echo "$name: $contents"
done
```

### 步骤 1：建立真实状态模型

从 terminal 输出建立"哪些技能在 category 里、哪些已提升、哪些是空壳"的数据结构。**不要在 execute_code 里做这个建模**。

### 步骤 2：识别重复和空壳

- **同名 SKILL.md 出现多次**：保留 depth 最浅的那个，删除其余
- **只剩 DESCRIPTION.md 的 category**：删除整个 category 目录
- **category 里还有技能的 SKILL.md**：先提升到根目录，再删 category
- **技能子目录已空**：直接 `rmdir`

### 步骤 3：批量操作（只用 terminal/shell）

用 Python 写操作脚本 → 保存到 `/tmp/` → 用 `bash /tmp/script.py` 执行，不通过 execute_code。

### 步骤 4：恢复 supporting content

从 hermes-agent 源码复制 references/scripts/templates：

```python
# 正确映射示例
# hermes-agent/skills/creative/comfyui/references
#   → ~/.hermes/skills/comfyui/references/
# hermes-agent/skills/creative/comfyui/scripts
#   → ~/.hermes/skills/comfyui/scripts/
```

注意路径映射：中间段的 category 名不出现，直接从 `技能名/` 开始。

### 步骤 5：验证

```bash
# 最终状态确认
find ~/.hermes/skills -maxdepth 1 -type d -exec test -f {}/SKILL.md \; -print | wc -l   # 技能总数
find ~/.hermes/skills -maxdepth 1 -type d -empty | wc -l   # 应为 0
find ~/.hermes/skills -name "SKILL.md" | awk -F'/' '{if(NF-1>7) print}' | wc -l  # 应为 0

# 抽样验证 supporting content
ls ~/.hermes/skills/comfyui/    # 应含 SKILL.md references/ scripts/
ls ~/.hermes/skills/p5js/      # 应含 SKILL.md references/ scripts/ templates/
```

## 关键约束

1. **terminal 唯一论**：所有文件系统操作（ls/find/cp/rm/mv）必须用 terminal，execute_code 只用于统计数据和建模分析
2. **先读后写**：任何写操作（cp/mv/rm）前必须先 terminal 确认真实状态
3. **分步验证**：每批操作后立即 terminal 验证，不要积累多个操作再一次性验证
4. **恢复前先建映射**：从源码恢复时先确认 src→dst 映射正确，避免把 `references/` 目录本身当技能复制

## execute_code 沙盒隔离问题

execute_code 的 venv 和真实 terminal 环境对 `~/.hermes/` 路径的读写**完全隔离**：
- execute_code 里 `os.listdir()` 看到的存在，terminal 可能看不到；反之亦然
- execute_code 里 `write_file`/`os.mkdir` 到 ~/.hermes/skills/ 不报错但静默失败
- `shutil.rmtree` 在 execute_code 里执行不会反映到真实文件系统

**所有对 ~/.hermes 路径的写操作必须用 terminal。**
