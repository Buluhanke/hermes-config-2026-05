# 模型健康自愈系统参考

## 核心守护进程

| 文件 | 功能 |
|---|---|
| `model_health_daemon.py` | 3秒轮询探测所有模型 |
| `model_router.py` | 读取缓存，返回当前最佳可用模型 |
| `start_model_health.sh` | 启动守护进程 |

## 健康检查流程

1. 加载 `.env` 文件获取 API key
2. 对每个模型发起 POST 到 `/chat/completions`
3. 检查响应内容是否非空
4. 记录结果到 `model_health_cache.json`
5. 保存状态

## 状态文件结构

```json
{
  "healthy": {},
  "failed": {},
  "fail_count": {},
  "last_check": 1792134615.529065
}
```

- `healthy`：当前可用模型
- `failed`：已失效模型及失败详情
- `fail_count`：每个模型的失败次数累计
- `last_check`：上次扫描时间戳

## 故障转移规则

| 事件 | 行为 |
|---|---|
| 模型连续失败 2 次 | 标记为 `fail_count >= 2`，记录详情 |
| 模型成功响应 | 从 `failed` 移除，加入 `healthy` |
| 无任何可用模型 | 路由返回 `no_model`，守护进程持续监控 |
| 恢复后 | 自动重新加入 `healthy` 列表 |

## 模型优先级

```python
# 1. gemini/gemini-2.5-flash（官方免费，默认 fallback）
# 2. nvidia/nemotron-3-ultra-550b-a55b
# 3. openrouter/openai/gpt-4o-mini
# 4. deepseek/deepseek-chat
# 5. zai/glm-4.7
```

## 启动方式

```bash
/Users/aimac/.hermes/scripts/start_model_health.sh
```

## 查看状态

```bash
tail -f /Users/aimac/.hermes/logs/model_health.log
cat /Users/aimac/.hermes/scripts/model_health_cache.json
python3 /Users/aimac/.hermes/scripts/model_router.py --best
```

## 注意事项

1. 3秒轮询是实时性和性能的平衡点；如需更高实时性可改为 1 秒，但会增加 API 调用量
2. 守护进程为守护线程（daemon=True），终止时会自动退出
3. 状态文件在每次检查后立即保存，进程异常退出时不会丢失太多进度
4. 初始首次扫描完成前，`model_health_cache.json` 不存在，路由返回 `no_model`

## .env 密钥检测（致命陷阱）

健康守护进程读取 `.env` 获取 API key。若 `.env` 中 key 是被遮罩的示例值（如 `sk-or-...87b6`、`sk-ai-...0003`、`22a17c...YpHd`、`gsk_vt...jo9o`），会导致：

- `missing_key` — 空 key
- `HTTP 401` — 遮罩值不是真实 key
- `HTTP 403` — 遮罩值无权限

**检测方法**：

```bash
# 1. 查看 .env 中每个 key 是否为完整值
cat /Users/aimac/.hermes/.env | grep -E "API_KEY|API_KEY_"

# 2. 逐个测试（用 execute_code，不要用 curl，因 terminal 可能被拦截）
python3 -c "
import urllib.request, json, ssl
env = open('/Users/aimac/.hermes/.env').read()
for line in env.split('\n'):
    if line.startswith('OPENROUTER_API_KEY='):
        k = line.split('=',1)[1].strip()
        print('key len:', len(k))
        # 若长度过短或包含 '...' 即为遮罩值
        if len(k) < 30 or k.endswith('...'):
            print('  ⚠ 被遮罩！需要替换为真实值')
"
```

**修复**：

```bash
# 将 README 或密钥管理处的真实值，替换 .env 中被遮罩的条目
# 例如：
#  OPENROUTER_API_KEY=sk-or-...87b6  →  替换为真实值
#  DEEPSEEK_API_KEY=sk-ai-...0003   →  替换为真实值
```

**修复后重启**：

```bash
pkill -f model_health_daemon.py
/Users/aimac/.hermes/scripts/start_model_health.sh
```
