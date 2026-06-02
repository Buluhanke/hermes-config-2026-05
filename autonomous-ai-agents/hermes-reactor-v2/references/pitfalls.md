# Pitfalls — 反应堆 v2/v3 踩过的坑

每个 pitfall 都有: 现象 / 根因 / 修复 / 防止复发的 guardrail。

---

## Pitfall 1: "开启新对话"被误识别为发送按钮

### 现象
```
[周期002] 阶段=READY
  🖱️  CLICK: (960, 437) '开启新对话今天Mac Mini自动化...'
```
点击了"开启新对话"按钮，而不是"发送"按钮。

### 根因
`div` 元素的 `innerText` 是所有子元素的合并文本。`t.includes('发送')` 永远返回 true。

### 修复
严格匹配 + 按宽度排序选最小的：
```python
if (t === '发送' || t === 'Send' || t === '提交'):
    candidates.push({x, y, text: t, w: rect.width})
candidates.sort((a, b) => a.w - b.w);  # 真按钮 60-100px，侧边栏 200px+
```

---

## Pitfall 2: Shadow DOM 屏蔽 stopBtn → 用 bodyLen 增长替代

### 修复
改用 `bodyLen` 增长信号：
```python
body_growing = current_body_len > last_body_len
```

---

## Pitfall 3: DeepSeek 慢思考 30-60s，过早 self_heal

### 修复
18 周期（36s）阈值 + 三重条件：
```python
if loading or body_len_growing: return False
if self.state["stuck_cycles"] >= 18: return True
if last_body_len == 0: return False  # 从没输出过=死了，不算卡
if bodyLen > last_body_len: return False  # 还在增长
return True
```

---

## Pitfall 4: F-string 反斜杠在 JS 模板中崩溃

### 修复
JS 模板字符串用 `"""..."""` + `+` 拼接，不用 f-string。

---

## Pitfall 5: CDP 消息格式错误

### 修复
Chrome CDP 不走 JSON-RPC，只用 `id` + `method` + `params`：
```python
await ws.send(json.dumps({"id": N, "method": "Runtime.evaluate", "params": {...}}))
```

---

## Pitfall 6: `Input.dispatchKeyEvent` text="" 双计数

### 修复
keyDown 只带 code，不带 text：
```python
{"type": "keyDown", "windowsVirtualKeyCode": 13, "key": "Enter", "code": "Enter"}  # 无 text
```

---

## Pitfall 7: body 阈值 800 导致短回复误判 RECREATE_TAB

### 修复
阈值从 800 降到 200：
```python
BODY_COMPLETE_THRESHOLD = 200
if body_len <= BODY_COMPLETE_THRESHOLD and no_growth_cycles >= 6:
    action = "RECREATE_TAB"
```

---

## Pitfall 8: RECREATE_TAB 直接关闭 WebSocket 导致 ConnectionClosedError

### 修复
用**任意活 tab 的 ws** 发 Page.navigate，避免直接关闭主 ws。

---

## Pitfall 9: PAGE_STUCK 在 AI 正常输出中被误触发

### 修复
三重条件必须同时满足：
```python
if stuck_cycles < 18: return False
if loading: return False
if last_body_len == 0: return False
if bodyLen > last_body_len: return False
return True
```

---

## Pitfall 10: minimaxi.com/v1/chat/completions 返回 404 ≠ 429

### 修复
- **429** = 账户额度耗尽 → 降级规则引擎
- **404** = 路由不存在
- **401** = Key 无效

---

## Pitfall 11: 记忆文件并发写入丢数据

### 修复
per-tab 命名 `hermes_memory_<tab>.json` 避免冲突。后续多实例需加 fcntl 锁或 SQLite。

---

## Pitfall 12: API 提供商悄然加锁（裸奔时代终结）

### 现象
```bash
# 昨天：SSL EOF 协议错误
# 今天：服务端正常但拒绝无认证请求 → {"error":{"message":"未提供令牌"...}}
```

### 根因
服务端加上了 token 认证，之前裸奔模式不再可用。

### 判断方法
```bash
# 返回模型列表 = 完全开放
# "未提供令牌" = 加锁但活着
# SSL/timeout = 真的死了
```

### Guardrail
- 第三方免费 API 随时可能加锁，判断活着与否用 `curl -s --noproxy '*' <base>/v1/models`（不加 key）
- 接到新 API 后立即记录认证状态

### 当前可用 API（2026-06-02 更新）
| 端点 | 状态 | 备注 |
|------|------|------|
| `https://api.minimaxi.com` | ✅ 活着 | M2.7，429=额度耗尽 |
| `https://api.deepseek.com` | ✅ 活着 | 免费额度有剩余 |
| `https://inference-api.nousresearch.com` | ❌ agent_key 过期 | 无法直调 |

---

## Pitfall 13: hermes config providers 交互界面遮蔽 API Key

### 现象
运行 `hermes config providers` → Custom endpoint → 填入 API key 后显示星号 `****`，无法验证是否存成功。

### 根因
交互界面填入的内容写入 `config.yaml` 的只是 `api_key_env: VAR_NAME`（变量名引用），不是实际 key 值。运行时从环境变量取，但 `.env` 里没有对应行。

### 修复
不依赖交互界面，直接手动编辑配置文件：
```bash
# 方案A（推荐）：直接追加到 .env
echo 'MINIMAX_CN_API_KEY=*** >> ~/.hermes/.env

# 验证
curl -s --noproxy '*' -H "Authorization: Bearer $MINIMAX_CN_API_KEY" \
  https://api.minimaxi.com/v1/models
```

### Guardrail
交互界面填 key 后，立即用 curl 验证：
```bash
# 返回模型列表 = key 有效
# "未提供令牌" = key 未存进去
```

---

## Pitfall 14: urllib SSL EOF / Python 3.14 TLS 不兼容

### 现象
```python
urllib.request.urlopen(req)  # SSL EOF
```

### 根因
urllib 的 SSL 握手与某些服务器不兼容，可能是 TLS 版本或 ALPN 协商差异。

### 修复
测试阶段用 `curl -s --noproxy '*'` 替代 Python urllib。
hermes_reactor_v3.py 内部已用 curl 做 API 调用，不受此影响。

---

## Pitfall 15: M3 模型 Key 授权范围 ≠ M2.7

### 现象
同一 API Key，M2.7 → 200 OK，M3 → 401 "无效的令牌"。

### 根因
中转盘的 Key 只能访问部分模型，不是全量开放。M3 未被授权。

### Guardrail
接入新模型必须逐个验证，不能假设同一 provider 下的模型全部可用。

---

## Pitfall 16: v2.aicodee.com 中转盘已废弃

### 现象
hermes_reactor_v3.py 残留 `v2.aicodee.com` 引用，`AICODEE_API_KEY` 环境变量。

### 修复
从 `.env` 和 `hermes_reactor_v3.py` 中彻底移除：
- 删除 `AICODEE_API_KEY` 行
- 删除 `https://v2.aicodee.com/v1` 相关代码
- base_url 切换为 `https://api.minimaxi.com/v1`

### Guardrail
接入新 API 后立即更新所有引用点，别让旧中转残留在代码库里。

---

## Pitfall 17: hermes config 交互界面 API Key 不持久化

### 现象
运行 `hermes config` → 填 API Key → 保存 → 再次 `hermes config show` 显示变量名引用而非实际 key。

### 根因
同 Pitfall 13，交互界面写入的是 `api_key_env: VAR_NAME` 引用，不是实际值。

### 修复
不依赖交互界面：
```bash
echo 'MINIMAX_CN_API_KEY=*** >> ~/.hermes/.env
```

### Guardrail
凡涉及 secrets，优先用 `echo` 直写 `.env`，交互界面只做展示和引导。