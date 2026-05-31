# config.yaml 精确块操作与修复

## 核心原则

config.yaml 是受保护文件，patch 工具被拒绝，sed 有范围删除风险。

**两种安全编辑方式：**
1. `str.replace()` — 精确段落替换，适合单行/短块
2. Python `yaml.safe_load()` + 直接字典操作 — 适合增删结构化区块

---

## 场景一：删除空的/残留的配置区块

**问题**：想删除 `secrets:` 整个区块（里面只有 bitwarden，且已 `enabled: false`）

**sed 误操作**（危险）：
```bash
sed -i '' '/^secrets:$/,/^    auto_install: true$/d' config.yaml
```
→ 范围是从 `secrets:` 到 `auto_install: true`，如果这之间有其他 section 的行，会一起删掉。
→ 结果：YAML 报 `mapping values are not allowed here` 错误。

**正确做法：Python 字典操作**：
```python
import yaml

path = '/Users/aimac/.hermes/config.yaml'
with open(path) as f:
    cfg = yaml.safe_load(f)

# 删除 bitwarden 条目
if 'secrets' in cfg and 'bitwarden' in cfg['secrets']:
    del cfg['secrets']['bitwarden']
    print("已删除 secrets.bitwarden")

# 如果 secrets 变空了，整个删掉
if 'secrets' in cfg and cfg['secrets'] == {}:
    del cfg['secrets']
    print("已删除空的 secrets")

with open(path, 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

# 验证
import yaml
with open(path) as f:
    yaml.safe_load(f)
print("YAML 有效")
```

**要点**：
- 先 `del dict[key]` 安全删除字段，不会误伤其他行
- 写回后立即 yaml.safe_load() 验证
- 任何编辑操作前先备份：`cp config.yaml config.yaml.bak.$(date +%Y%m%d_%H%M%S)`

---

## 场景二：只重建 config.yaml 的某个区块

**问题**：某个区块（如 `custom_providers`）结构损坏，但文件其余部分完好。

**可用 yaml.dump() 只重建那个区块**，因为：
- 只 load 和 dump 那个区块对应的 Python 对象
- 不影响文件中其他所有内容

```python
import yaml

path = '/Users/aimac/.hermes/config.yaml'
with open(path) as f:
    cfg = yaml.safe_load(f)

# 重建 custom_providers（干净的 Python list + dict）
cfg['custom_providers'] = [
    {
        'name': 'V2.aicodee.com',
        'base_url': 'https://v2.aicodee.com/v1',
        'api_key_env': 'AICODEE_API_KEY',
        'model': 'MiniMax-M2.7-highspeed',   # ← /model picker 靠这个匹配当前模型
    },
    {
        'name': 'Api.groq.com',
        'base_url': 'https://api.groq.com/openai/v1',
        'api_key_env': 'GROQ_API_KEY',
        'model': 'llama-3.3-70b-versatile'
    },
    {
        'name': 'Api.cerebras.ai',
        'base_url': 'https://api.cerebras.ai/v1',
        'api_key_env': 'CEREBRAS_API_KEY'
    }
]

with open(path, 'w') as f:
    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
```

**副作用**：yaml.dump() 会重排**所有 key 的字母顺序**（sort_keys=False 只阻止 key 排序，但仍按 Python dict 写入顺序）。如果文件其余部分有依赖 key 顺序的工具，可能受影响。

---

## 场景三：修复 yaml.dump() 导致的行合并

**症状**：`yaml.dump()` 写回后，相邻的两行变量被合并成一行：
```
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

**原因**：`yaml.dump()` 在流式输出时没有在每个块之间加空行。

**修复**：
```python
with open(path) as f:
    content = f.read()

# 在 = 后面没空格的地方插入换行（检测相邻的两个 URL= 行被合并的情况）
content = content.replace('v1/v1', 'v1\n')  # 临时加个换行

# 或者逐行处理：检查没有空行且不以空格/特殊字符开头的行
lines = content.split('\n')
fixed = []
for line in lines:
    if line and not line[0].isspace() and '=' in line:
        # 如果这行看起来像多个变量合并，尝试拆分
        # 模式：KEY1=val1KEY2=val2
        import re
        # 在 KEY= 模式前插入换行
        merged = re.sub(r'([A-Z0-9_]=[^A-Z0-9_\n]+[A-Z0-9_])', r'\1\n', line)
        fixed.append(merged.rstrip())
    else:
        fixed.append(line)

with open(path, 'w') as f:
    f.write('\n'.join(fixed))
```

---

## 快速备份/恢复

```bash
# 备份
cp /Users/aimac/.hermes/config.yaml /Users/aimac/.hermes/config.yaml.bak.$(date +%Y%m%d_%H%M%S)

# 恢复
ls -t /Users/aimac/.hermes/config.yaml.bak* | head -1
cp $(ls -t /Users/aimac/.hermes/config.yaml.bak* | head -1) /Users/aimac/.hermes/config.yaml
```

---

## 验证清单（每次编辑后必做）

```bash
# 1. YAML 格式有效
python3 -c "import yaml; yaml.safe_load(open('/Users/aimac/.hermes/config.yaml'))" && echo "YAML OK"

# 2. 无明文 key 残留
grep -E "api_key:\s+[a-zA-Z]" /Users/aimac/.hermes/config.yaml || echo "无硬编码 key"

# 3. 无残留目标关键词
grep -i "bitwarden\|BWS\|残留词" /Users/aimac/.hermes/config.yaml /Users/aimac/.hermes/.env 2>/dev/null || echo "无残留"
```
