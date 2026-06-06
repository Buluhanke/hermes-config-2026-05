# macOS BSD sed "假成功" 复现 + 绕开 (2026-06-06 验证)

## 30 秒复现

```bash
# 准备测试文件
echo "hello world" > /tmp/sed_test.txt
cat /tmp/sed_test.txt
# hello world

# 跑 BSD sed
sed -i '' 's|hello|goodbye|' /tmp/sed_test.txt
echo "exit: $?"

# 看结果
cat /tmp/sed_test.txt
# ⚠️ macOS 13+ 上可能仍是 "hello world"（没改！）
# 但 exit code = 0，所以你的脚本会接着打印 "✅ 改完"
```

**真相**：BSD `sed -i ''` 在某些 macOS 版本上**默默吞掉**空 backup 后缀的整段参数解析，**匹配 0 次但 exit 0**。

## 验证脚本（诊断你的 macOS sed 是否中招）

```bash
# ~/.hermes/scripts/diagnose_bsd_sed.sh
TEST=/tmp/sed_test_$$
echo "original content with old_value" > $TEST

# GNU 风格（Linux 这么写）
sed -i 's|old_value|new_value|g' $TEST
GNU_RESULT=$(cat $TEST)

# BSD 风格（macOS 默认）
echo "original content with old_value" > $TEST  # 重置
sed -i '' 's|old_value|new_value|g' $TEST
BSD_RESULT=$(cat $TEST)

echo "GNU 改后: $GNU_RESULT"
echo "BSD 改后: $BSD_RESULT"

if [ "$GNU_RESULT" = "original content with new_value" ] && [ "$BSD_RESULT" = "original content with new_value" ]; then
    echo "✅ sed 正常"
elif [ "$GNU_RESULT" = "original content with new_value" ] && [ "$BSD_RESULT" = "original content with old_value" ]; then
    echo "❌ BSD sed 假成功！改用 Python / perl / gsed"
fi
rm -f $TEST
```

## 3 个绕开方案（按推荐度排序）

### 1. Python（最稳，所有 macOS 通用）

```bash
~/.hermes/hermes-agent/venv/bin/python << 'PYEOF'
path = '/path/to/file'
with open(path) as f:
    content = f.read()
content = content.replace('old', 'new')
with open(path, 'w') as f:
    f.write(content)
PYEOF
```

### 2. `perl -pi -e`（Perl 在 macOS 自带，行为稳定）

```bash
perl -pi -e 's|old|new|g' /path/to/file
```

### 3. `gsed`（GNU sed via brew）

```bash
brew install gnu-sed
gsed -i 's|old|new|g' /path/to/file  # 行为和 Linux 一致
```

## 任何 sed 改完的"3 行验证"模板

```bash
# 改前数
BEFORE=$(grep -c "明文模式" file.yaml)
# 改
sed -i '' 's|old|new|g' file.yaml
# 改后数（必跑！）
AFTER=$(grep -c "明文模式" file.yaml)
[ "$BEFORE" = "$AFTER" ] && echo "❌ 假成功，绕开 sed"
```

## 触发场景清单（遇到这些，**别用 BSD sed**）

- 改 `.yaml` / `.toml` / `.json` / `.ini` 配置文件
- 改 Python/JS 源码里的字串
- 改任何有特殊字符的（`$`、`\`、`{`、`}`）
- 一次改多处（`g` flag 触发 BSD 解析错位概率上升）
- 改了之后会立刻有下游读取这个文件（`hermes config show`、`docker compose up` 等）

## 反面教材（6/6 凌晨真实事件时间线）

```
00:13 备份建好
00:14 跑 sed -i '' 's|api_key: sk-290...|api_key: ${...}|' config.yaml
      → 打印 "✅ 改完"
      → 实际: 0 处被改（BSD sed 默默吞掉）
00:15 跑 9 处 sed 一次性
      → 报错 "command c expects \ followed by text"
      → 暴露: 第一次的"成功"也是假
00:20 改用 Python 一次性 9 处全改成功
      → 改前 10 处 → 改后 0 处
      → 真实成功
```

## 教训

- **`echo "✅"` 是你的，不是 sed 的**
- **改完不 grep 验证 = 没改**
- **复杂的 sed 表达式直接用 Python**——5 行 Python 比 1 行 sed + 3 行验证更省事

详见 `proactive-execution` 规则 31。
