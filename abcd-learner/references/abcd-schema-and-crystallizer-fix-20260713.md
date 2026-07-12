# ABCD 学习流水线关键修复记录（2026-07-13）

## B_insight → fact_store 的 schema 真相

| 字段 | 真相 | 之前错误认知 |
|------|------|------------|
| `content` | fact长描述文本（要升华成skill body的内容） | 以为是分类 |
| `category` | fact分类名（如"general", "arxiv-insight"） | 以为是长描述 |
| `tags` | 逗号字符串如 `"star4d,learning"`，**不是JSON数组** | 当JSON解析导致首条崩溃 |
| `retrieval_count` | 被检索次数，新fact=0 | — |
| `trust_score` | 0.00-1.00，新写入默认0.70 | — |

## 升华门槛修复：从 ≥3 降到 ≥1

**原问题**：新知识的 retrieval_count=0，永远达不到≥3门槛，导致 fact_store 里的知识永远无法变成 skill。

**修复**：在 wrapper 的 E 阶段前加 E2 反思消化步骤：
```python
# 新知识立即被"引用"一次，retrieval_count 从 0 变成 1
conn.execute("UPDATE facts SET retrieval_count=retrieval_count+1 WHERE ...")
```

## body 字段修复

`write_skill()` 函数里：
```python
# 错误（之前）
body = category if category else content
# 正确（2026-07-13修复）
body = content if content else (category or "")
```

## tags 解析修复

```python
def _parse_tags(raw):
    if not raw or not raw.strip():
        return []
    if raw[0] in '["':          # JSON数组格式
        try:
            return json.loads(raw)
        except Exception:
            pass
    return [t.strip() for t in raw.split(',') if t.strip()]  # 逗号字符串格式
```

## E2 反思消化代码位置

`idle_learning_wrapper.sh` 的 E2 步骤，在 `cve_lite` 之后、`fact_store统计` 之前。升华条件：
- `retrieval_count >= 1`（新知识被引用过）
- `trust_score >= 0.65`
- `retrieval_count != -999`（尚未固化）

升华后 fact 标记 `retrieval_count=-999`，不再重复升华。
