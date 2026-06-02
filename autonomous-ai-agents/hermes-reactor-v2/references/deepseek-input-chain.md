# DeepSeek Input Chain — 6次验证成功 (2026-06-02)

## 完整链路（已验证 6/6 次）

```
browser_cdp (WebSocket)
  → Target.getTargets → 找到 deepseek tab
  → Runtime.evaluate: textarea.focus()
  → Input.dispatchKeyEvent 逐字 (keyDown→char→keyUp, 0.05s间隔)
  → Input.dispatchKeyEvent Enter
  → 监听 WebSocket SSE 天眼流
  → 解析 DeepSeek patch 协议
  → 返回完整回复
```

## 关键参数

- **Tab 匹配**: `url: "deepseek.com"` 或标题含 "DeepSeek"
- **Textarea selector**: `document.querySelector('textarea')`
- **发送按钮**: 严格 `=== '发送'` 或 `'Send'`，按 `width` 排序取最小
- **Enter 兜底**: 找不到按钮时自动用 Enter
- **SSE 解析**: DeepSeek 用 `{"v": "x"}` 和 `{"p":..,"o":"APPEND","v":"x"}` 两种 patch 格式
- **完成检测**: `bodyLen` 增长停止 12 周期（24s）= 真卡住

## 命令行

```bash
cd ~/.hermes/scripts
python3 network_sniffer.py deepseek "1+1等于几"
python3 hermes_reactor_v2.py deepseek 25 "什么是云计算"
```

## 已知限制

- 网络波动时 SSE 可能断开，需要重连（代码内已有重连逻辑）
- DeepSeek 慢思考模式 30-60s，阈值 18 周期（36s）足够