# Hindsight Python Client 实战（2026-06-02）

## 状态

- Docker容器 `hermes-hindsight` 运行中，端口8899 ✅
- `hindsight_client` Python库已安装到hermes-agent venv ✅
- 连通验证通过 ✅

## 验证命令

```python
~/.hermes/hermes-agent/venv/bin/python -c "
from hindsight_client import Hindsight
c = Hindsight('http://127.0.0.1:8899')
r = c.recall(bank_id='hermes', query='hello')
print([x.text for x in r.results])
"
```

## API正确用法

```python
from hindsight_client import Hindsight
c = Hindsight('http://127.0.0.1:8899')

# 搜索记忆（bank_id必须显式传）
r = c.recall(bank_id='hermes', query='关键词')
for result in r.results:
    print(result.text)

# 存储记忆
c.retain(bank_id='hermes', content='记忆内容', tags=['标签1', '标签2'])

# 反思
r = c.reflect(bank_id='hermes', query='问题描述')
print(r.text)
```

## 坑

- `Hindsight()` 构造函数不需要 `bank_id` 参数
- `bank_id` 必须在 `recall()` / `retain()` / `reflect()` 方法中传入
- 旧版用法错误：`Hindsight('url', 'bank_id')` → `TypeError`
