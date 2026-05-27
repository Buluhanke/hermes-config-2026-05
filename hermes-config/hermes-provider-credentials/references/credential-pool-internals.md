# Credential Pool 内部结构（调试笔记）

## auth.json credential_pool 条目结构

每条 credential 包含以下字段：

```json
{
  "id": "6位hex",
  "label": "显示名称",
  "auth_type": "api_key",
  "priority": 0,          // 0=最高, 数字越大优先级越低
  "source": "config:X | manual | env:VAR_NAME | model_config",
  "last_status": "ok | exhausted | error | None",
  "last_status_at": UnixTimestamp,
  "last_error_code": 429,
  "last_error_reason": "rate_limit_error",
  "last_error_message": "详细错误信息",
  "last_error_reset_at": UnixTimestamp,
  "base_url": "https://...",
  "request_count": 0,
  "api_key": "",          // 部分条目有，部分为空
  "access_token": "YOUR_API_KEY...", // 实际使用的 key
  "secret_fingerprint": "sha256..." // 仅 env 来源有
}
```

## 发现过程

### 如何查看所有 provider 状态
```python
import json
with open('/Users/aimac/.hermes/auth.json') as f:
    a = json.load(f)
cp = a.get('credential_pool', {})
for k, v in sorted(cp.items()):
    if v:
        s = str(v[0].get('last_status', '?'))
        src = str(v[0].get('source', '?'))
        bu = str(v[0].get('base_url', '?'))
        print(f'{k:50s} status={s:15s} source={src:25s} base={bu}')
```

### 如何检查 key 是否更新成功
```python
t = 'custom:目标provider'
at = cp[t][0].get('access_token', '')
print(f'Key length: {len(at)}, starts_with_sk: {at.startswith("YOUR_API_KEY")}')
```

### v2.aicodee.com 相关 provider 列表
这些 provider 共享同一个 AICODEE_API_KEY：
- `custom:aicodee` — 直接 aicodee 线路
- `custom:aicodee-relay` — aicodee 中继
- `custom:v2.aicodee.com` — v2.aicodee.com 线路
- `custom:minimax-relay-(v2.aicodee.com)` — MiniMax 通过 aicodee 中继

更新 key 时这 4 个 provider 共 7 条 credential 需要一起更新。
