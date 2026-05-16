# 超级鹰打码平台参考

## 价格（2025年实测）

| 套餐 | 价格 | 折合每题 |
|------|------|---------|
| 1元/1000题 | ¥1 | ¥0.001 |
| 10元/10000题（5折） | ¥10 | ¥0.001 |
| 50元/50000题（3.3折） | ¥50 | ¥0.0007 |

**推荐**：先买1元测试，接入确认稳定后再买大套餐。

## 注册地址

官网：chaojiying.com
用户中心 → 软件ID（softid）→ API文档

## 验证码类型代码

| 类型 | code | 说明 |
|------|------|------|
| 英文数字 | 1902 | 最便宜，字符型 |
| 中文汉字 | 5000 | 点选，复杂 |
| 滑动拼图 | 5000 | 拖动 |
| 计算题 | 20400 | 如"3+5=?" |

## Python 接入模板

```python
import requests, base64, json

def solve_captcha(image_path: str, captcha_type: str = "1902") -> str:
    """超级鹰打码，返回识别结果"""
    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "user": "YOUR_USER",
        "pass": "YOUR_PASS",        # 密码MD5后传输
        "softid": "YOUR_SOFTID",
        "codetype": captcha_type,
        "file_base64": img_base64
    }

    r = requests.post(
        "http://upload.chaojiying.net/Upload/Processing.php",
        data=payload, timeout=30
    )
    result = r.json()
    if result["err_str"] == "OK":
        return result["pic_str"]
    else:
        raise Exception(f"打码失败: {result['err_str']}")
```

## 滑块验证码本地方案（零成本）

对于简单的拼图滑块，可以不用打码平台：

```python
from humanization_core import capture_screen, ask_vlm
import pyautogui, re

img_path = capture_screen()
vlm_response = ask_vlm(img_path, "找到滑块缺口的x坐标，回复纯数字")
x = int(re.search(r'\d+', vlm_response).group())
pyautogui.moveTo(start_x, start_y)
pyautogui.mouseDown()
# 贝塞尔曲线拖动，分段带随机停顿
pyautogui.mouseUp()
```

**何时选本地 vs 打码平台**：滑动轨迹简单用本地；复杂拼图/点选用超级鹰。
