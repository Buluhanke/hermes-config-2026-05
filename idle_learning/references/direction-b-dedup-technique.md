# Direction B 论文去重技术 (Dedup Technique)

## 问题

每次 direction B 全量扫描 OSU-NLP YAML（537 papers）后，Desktop 过滤仍有 ~78 篇。
手动检查每篇是否已被现有 references 覆盖成本高、易出错。

## 解决方案

写一个 Python 脚本维护 `KNOWN_ARXIV` 集合，每次扫描时自动标记 KNOWN vs NEW。

### 核心逻辑（3 步）

```
1. 获取 YAML → curl raw.githubusercontent.com
2. 解析并过滤 → Desktop + 关键词评分 ≥ 2  
3. 去重 → arxiv_id 前 7 位匹配 KNOWN_ARXIV 集合
```

### 去重匹配规则

```python
def is_known(arxiv_id):
    """7-char prefix match on arxiv ID (works for 25xx.xxxxx format)."""
    aid = arxiv_id.replace('.', '').replace('-', '')[:10]
    for known in KNOWN_ARXIV:
        k = known.replace('.', '').replace('-', '')[:10]
        if len(aid) >= 7 and len(k) >= 7 and aid[:7] == k[:7]:
            return True
    return False
```

**为什么用前 7 位**：arxiv ID 格式为 `YYMM.NNNNN`，前 5 位是年月，第 6-7 位是序列号前缀。
匹配前 7 位（`YYMM.NNN`）覆盖同一天提交的同系列论文。
注意：`2404.11.11-OSWorld` 这种带后缀的 ID 需手动处理，脚本自动剥离非数字部分。

### 已知论文库的维护

`KNOWN_ARXIV` 集合需要随新 reference 文件扩展：
- 每次方向 B 扫描后，将新发现的 arxiv_id 加入集合
- 脚本路径：`scripts/direction-b-scan.py`
- 如果不更新 KNOWN_ARXIV，下次扫描会重复报告同一篇为 NEW

### 饱和检测

当 `new_count == 0` 时，脚本返回 exit code 1 并打印 `[SATURATED]`。
调用方应检测 exit code 并跳过全量扫描转为增量模式。

### 实测发现量趋势

| 扫描 | 日期 | 模式 | 新发现 |
|------|------|------|--------|
| #1 | 2026-06-01 | 全量 | ~30 篇 |
| #2 | 2026-06-02 早 | 全量 | 11 篇 |
| #3 | 2026-06-02 晚 | 全量 | 9 篇 |
| #4+ | 后续 | 增量(30条) | 预计 0-3 篇 |

**饱和判定**：连续 2 次扫描新发现 < 3 篇 → 转为增量模式（仅检查前 30 条）。
