# hermes_desktop_rpa.py OCR 报错 "Argument list too long"

## 问题

```bash
python3 hermes_desktop_rpa.py ocr 400,200,1500,800
# OSError: [Errno 7] Argument list too long: 'curl'
```

hermes_desktop_rpa.py 的 `ocr` 动作将截图 base64 编码后，通过 subprocess curl 的命令行参数传递。macOS 命令行参数长度限制约 262KB，截图转 base64 后远超此限制。

## 根因

```python
# hermes_desktop_rpa.py 第 92 行 (ocr 函数)
out, err, code = run([
    "curl", "-s",
    ocr_url,
    "--data-urlencode", f"image={b64}"  # b64 是完整 base64 字符串
], timeout=30)
```

## 解法

用 Python urllib 直接发 POST 请求，不走命令行参数：

```python
import subprocess, json, base64, os, urllib.request, urllib.parse

# 1. 截图
subprocess.run([
    "screencapture", "-x", "-R400,200,1500,800", "/tmp/ocr_input.png"
], capture_output=True, timeout=15)

# 2. 读取 .env 获取 Baidu OCR 凭据
env = {}
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip()

# 3. 获取 access_token
token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={env.get('BAIDU_API_KEY')}&client_secret={env.get('BAIDU_SECRET_KEY')}"
req = urllib.request.Request(token_url, data=b"", method="POST")
with urllib.request.urlopen(req, timeout=10) as resp:
    access_token = json.loads(resp.read())["access_token"]

# 4. 调用 OCR（Python urllib，不走命令行）
with open("/tmp/ocr_input.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
data = urllib.parse.urlencode({"image": b64}).encode()
req = urllib.request.Request(ocr_url, data=data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")

with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read())
    for r in result.get("words_result", []):
        print(r.get("words", ""))
```

## 临时 workaround（不改脚本）

在 execute_code 中用上面代码直接调用 OCR，不经过 hermes_desktop_rpa.py 的 ocr 动作。
