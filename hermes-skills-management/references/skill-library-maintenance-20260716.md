# Skills Library Self-Maintenance SOP

## 何时需要维护

- 发现skill埋在子目录里导致检索不到
- 发现多个重复的旧版存档
- fact_store里出现大量retrieval_count=-999的知识
- curator把重要skill归档了但还在用

## 深度检查命令

```bash
# 1. 查看所有skill的深度分布
find ~/.hermes/skills -mindepth 1 -maxdepth 1 -name "SKILL.md"   # depth-1（应该最多）
find ~/.hermes/skills -mindepth 2 -maxdepth 2 -name "SKILL.md"   # depth-2（正常）
find ~/.hermes/skills -mindepth 3 -maxdepth 3 -name "SKILL.md"   # depth-3（埋太深！）

# 2. 检查空壳目录（无SKILL.md）
for d in ~/.hermes/skills/*/; do
  name=$(basename "$d")
  [[ "$name" == .* || "$name" == _* ]] && continue
  [[ -f "$d/SKILL.md" ]] && echo "✅ $name" || echo "❌ $name"
done

# 3. 查看.archive存档
ls ~/.hermes/skills/.archive/ | wc -l   # 总量
ls ~/.hermes/skills/.archive/            # 列出所有

# 4. 对比活跃 vs 归档
ls ~/.hermes/skills/ | grep -v "^\." | grep -v "^_" | grep -v "\.md$" | sort > /tmp/alive.txt
ls ~/.hermes/skills/.archive/ | sort > /tmp/archived.txt
comm -12 /tmp/alive.txt /tmp/archived.txt   # 活着且有归档的
comm -23 /tmp/archived.txt /tmp/alive.txt   # 纯孤儿（活跃里没有对应物的）

# 5. 检查重复存档（按名称关键词）
ls ~/.hermes/skills/.archive/ | grep "关键词" | sort
```

## 扁平化 SOP（depth-3 → depth-1）

**危险警告：rm -rf 父目录前必须先完成所有 mv，否则会删掉正在移动的skill！**

正确顺序：
```bash
# Step 1: 先 mv 到顶层
mv ~/.hermes/skills/category/deep-skill ~/.hermes/skills/deep-skill

# Step 2: 再删空壳父目录
rmdir ~/.hermes/skills/category  # 只在目录空时用 rmdir
# 或
rm -rf ~/.hermes/skills/category  # 确认所有内容已移走再用
```

**错误顺序（会丢数据）：**
```bash
# ❌ 危险：先删父目录 → mv 目标消失 → skill 被删
rm -rf ~/.hermes/skills/category
mv ~/.hermes/skills/category/deep-skill ~/.hermes/skills/deep-skill  # 失败！
```

## 重复存档清理

```bash
ARCH=~/.hermes/skills/.archive

# 例：保留最新的"小时工具错误聚集"
ls "$ARCH" | grep "小时工具错误聚集" | sort    # 列出全部
ls "$ARCH" | grep "小时工具错误聚集" | grep -v "20260716"  # 找旧版
# 删除旧版
for f in $(ls "$ARCH" | grep "小时工具错误聚集" | grep -v "20260716"); do
  rm -rf "$ARCH/$f"
done
```

## Archive 恢复

**只在以下情况恢复：**
1. skill被index引用但被归档了
2. skill在当前活跃skills里不存在

```bash
# 恢复被误归档的skill
cp -r ~/.hermes/skills/.archive/<skill-name> ~/.hermes/skills/<skill-name>
```

**不需要恢复的：** 纯时间序列日志类skill（如各日"小时工具错误聚集"）、已被同名活跃skill覆盖的旧存档。

## Curator 行为备忘

- curator 自动归档 `created_by: agent` 且14天无检索的skill
- `created_by: hermes-curator` 的是 curator 自己生成的，也不免疫
- 保护方法：写到 `~/.hermes/skills/<name>/` 根目录（不是子目录），确保被检索到
- 或者把关键知识写成代码函数（不依赖检索）

## 今日整改记录（2026-07-16）

- 删除了10个空壳category（apple/creative/data-science/email/media/mlops/note-taking/productivity/smart-home/social-media）
- 删除了9个重复"小时工具错误聚集"旧存档
- 从.archive恢复了：anysearch, dossier, pulse, litreview, grants
- 11个埋藏skill全部提升到顶层
- 最终：30个真实skill全部depth=1
