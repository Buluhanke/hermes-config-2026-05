# config.yaml 编辑规范

## 铁律：不用 sed 改 YAML

sed 对多行结构、嵌套缩进的替换极容易搞坏 YAML。YAML 是缩进敏感的，sed 匹配换行/多行时行为不可预测。

**正确做法：用 Python 做精确替换**

```python
python3 << 'PYEOF'
with open('/Users/aimac/.hermes/config.yaml') as f:
    content = f.read()
content = content.replace('old_string', 'new_string', 1)
with open('/Users/aimac/.hermes/config.yaml', 'w') as f:
    f.write(content)
PYEOF
```

**备份永远是第一位**：
```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d_%H%M%S)
```

**恢复**：`ls -t ~/.hermes/config.yaml.bak* | head -1` 找最新备份 `cp <backup> ~/.hermes/config.yaml`

## 本次教训（2026-05-29）
- `sed -i '' 's/A/B/'` 改 provider 时多处中招
- `yaml.dump()` 改变了原有结构，key 被吞
- 解法：备份 → Python 精确替换 → 逐行验证 → 重启 gateway
