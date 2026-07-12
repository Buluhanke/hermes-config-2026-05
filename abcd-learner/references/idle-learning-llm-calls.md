# Idle Learning LLM 调用模式（2026-07-12 实测）

## MiniMax API 直接调用

**端点**：`http://123.56.67.77:9100/v1/chat/completions`
**模型**：`MiniMax-M2.7-highspeed`
**Key**：`~/.hermes/.env` → `MINIMAX_M3_API_KEY`

```python
import urllib.request, json, re

def get_minimax_key():
    env = pathlib.Path.home() / ".hermes" / ".env"
    for line in env.read_text().splitlines():
        if "MINIMAX_M3_API_KEY" in line:
            m = re.search(r'"([^"]+)"', line)
            if m:
                return m.group(1)
    return ""

key = get_minimax_key()
url = "http://123.56.67.77:9100/v1/chat/completions"
payload = {
    "model": "MiniMax-M2.7-highspeed",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 300,
    "temperature": 0.3,
}
req = urllib.request.Request(url,
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    method="POST")
with urllib.request.urlopen(req, timeout=20) as resp:
    content = json.loads(resp.read())["choices"][0]["message"]["content"]
```

**超时**：必须 20s，10s 会 timeout

---

## execute_code sandbox vs terminal 环境差异

| | execute_code 沙盒 | terminal |
|--|---|---|
| `~/.hermes/.env` 读得到 | ✅ | ✅ |
| MiniMax API `123.56.67.77:9100` | ✅ | ✅ |
| Gateway 进程内 env var | ❌ | ✅ |
| Gateway 端口 8642 | ❌ | ✅ |

**结论**：MiniMax API 从 execute_code 可以直接调（不需要 gateway 进程内环境变量）。

---

## 写文件到 ~/.hermes 的正确方式

`execute_code` 的 Python 沙盒写入 `~/.hermes/scripts/` 是**隔离进程**：
- `pathlib.Path("~/.hermes/scripts/b_insight.py").write_text()` → 文件存在，但路径是沙盒内
- 实际应写到 `/Users/aimac/.hermes/scripts/b_insight.py`

**正确方式**：在 execute_code 里用绝对路径写文件，不要用 `~` 展开。

---

## B_insight 完整流程

```
wrapper.sh → orchestrator（B_paper 写论文入库）
          → b_insight.py（读DB论文 → MiniMax推理 → 写洞察到DB）
          → cve_lite.py
          → abcd_learner.py
          → batch_facts_from_log.py
```

**b_insight.py 必须先写入盘**（`~/.hermes/scripts/b_insight.py`），wrapper 才能调用到。
