# 工程整合路径发现 (2026-05-13)

## CDP执行路径（实际，非预期）

```
browser_click(ref="@e5")
  → _run_browser_command(task_id, "click", ["@e5"])
      → subprocess.run([agent-browser, "click", "@e5"])
          → agent-browser CLI 内部通过 CDP WebSocket 控制浏览器
```

**关键发现：** agent-browser CLI 是代理，鼠标移动由 CLI 内部处理，Python 层只发送命令字符串。无法直接从 Python 注入贝塞尔曲线到 CLI 内部。

## 两条整合路线

### 路线A：browser_cdp 绕过CLI（需要tab_id）

```python
# 1. 获取当前tab的target_id
tab_info = browser_cdp(method="Target.getTargets", params={})

# 2. 用 browser_cdp 发贝塞尔轨迹（绕过agent-browser CLI）
for point in trajectory:
    browser_cdp(
        method="Input.dispatchMouseEvent",
        params={"type": "mouseMoved", "x": point[0], "y": point[1]},
        target_id=target_id
    )
```

### 路线B：Camofox 反检测浏览器

Camoufox 是 Firefox 分支，原生反指纹。**已知问题（macOS 26.4.1）：** binary v135.0.1-beta.24 启动挂起。

## Telegram 验证工作流

任何技能整合之前，**必须先验证通信通道畅通**。

```python
import requests
proxies = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
resp = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={"chat_id": HOME_CHANNEL, "text": "🧪 Hermes 连接测试"},
    proxies=proxies, timeout=10
)
assert resp.json()["ok"]
```

常见失败：直连被重置（走代理）、403 Bot未/start、401 Token错误。

## 三个技能模块现状（2026-05-13创建）

| 模块 | 路径 | 状态 |
|------|------|------|
| humanization_engine | `skills/engineering/humanization_engine/` | ✅ 可导入 |
| resilience_engine | `skills/engineering/resilience_engine/` | ✅ 可导入 |
| desktop_consciousness | `skills/engineering/desktop_consciousness/` | ✅ 可导入 |

验证：
```bash
python3 -c "
import sys; sys.path.insert(0, '/Users/aimac/.hermes/skills/engineering')
from humanization_engine import generate_human_trajectory
from resilience_engine import Watchdog
from desktop_consciousness import get_session_state
print('✅ all three modules importable')
"
```
