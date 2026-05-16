# Desktop Vision Workaround

当 Hermes 主模型（DeepSeek-v4-flash / MiniMax-M2.7-highspeed）**不支持视觉/图片输入**时，可通过本机的 Gemini 代理读取截图内容。

## 适用场景

- 需要 AI "看到"桌面内容（向日葵验证码、窗口文本、错误弹窗等）
- 主模型不支持 `image_url` 参数（vision_analyze 报错 `unknown variant 'image_url'`）
- 不可安装系统级 OCR（无 Homebrew、无 tesseract 二进制）

## 前置条件

1. **macOS 屏幕录制权限**已开启
   - 系统设置 → 隐私与安全性 → 屏幕录制 → Terminal（或其他终端）打钩

2. **Gemini 本地代理**正在运行（`script/gemini-proxy.py`）
   ```bash
   GEMINI_API_KEY=你的key python3 gemini-proxy.py
   ```
   代理监听 `http://127.0.0.1:8899/v1`，支持 OpenAI 兼容格式 + Gemini 原生格式

## 工作流

### 1. 截图

```bash
screencapture -x /tmp/screen.png
# 或指定显示器（多显示器时）
screencapture -x -D 1 /tmp/screen.png
```

成功的截图特征：700KB+，1920×1080，PNG RGBA。若文件极小（<50KB），说明权限未生效或截图为空。

### 2. 通过 Gemini 代理读图

```python
import base64, json, urllib.request

with open("/tmp/screen.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "gemini-3.1-flash-lite-preview",  # 或 gemini-2.5-flash
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "描述这张图的内容，特别关注数字和代码"},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
    ]}],
    "max_tokens": 1000
}

req = urllib.request.Request(
    "http://127.0.0.1:8899/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    content = result["choices"][0]["message"]["content"]
```

## 关键发现

### 哪些模型/端点支持 vision

| 模型/端点 | 支持 vision? | 备注 |
|-----------|-------------|------|
| DeepSeek-v4-flash (api.deepseek.com) | ❌ | 400 Bad Request — 不支持 image_url |
| MiniMax-M2.7-highspeed (v2.aicodee.com) | ❌ | 400 — 错误 `unknown variant image_url` |
| aicodee (v2.aicodee.com) | ❌ | 余额 $0 — 即使支持也无额度 |
| Gemini proxy (127.0.0.1:8899) | ✅ | gemini-2.5-flash / gemini-3.1-flash-lite-preview 均支持 |
| Groq (llama-3.1-8b-instant) | ❌ | 文本模型 |
| NVIDIA (llama-3.3-70b) | ❌ | 文本模型 |

### base64 data URL 格式

```text
data:image/png;base64,<base64字符串>
```

- PNG 图片 base64 编码后文件大小约增加 33%（700KB PNG → ~930KB base64）
- Gemini 代理（本地 127.0.0.1:8899）无大小限制
- 避免使用外部 URL（非 HTTPS 可能被拒绝）

### 大图处理

1920×1080 全屏截图 ~700KB PNG，base64 后约 930KB。Gemini 代理处理耗时约 6-15 秒。

若需加速，可先压缩：
```bash
sips -s format jpeg -s formatOptions 60 /tmp/screen.png --out /tmp/screen.jpg
# 700KB → ~200KB，质量可接受
```

## 已知 pitfall

- **screencapture 失败返回黑屏**：通常是 macOS 屏幕录制权限未授予。检查系统设置 → 隐私与安全性 → 屏幕录制，确认 Terminal 已勾选。
- **Gemini 代理未启动**：访问 127.0.0.1:8899 超时或 Connection refused。`ps aux | grep gemini-proxy` 检查进程。
- **Gemini API key 过期**：代理返回 400 INVALID。重新获取 key 后重启代理。
- **aicodee 余额不足**：即使 vision 调用成功也需要账户余额。检查 aicodee 控制台。
- **base64 数据太大**：偶尔可能触发 Gemini 的输入限制。必要时先压缩图片尺寸。
