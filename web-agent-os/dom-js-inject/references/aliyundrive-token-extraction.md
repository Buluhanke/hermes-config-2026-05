# Aliyun Drive token 提取

**日期**: 2026-06-01
**问题**: 阿里云盘网页登录后，需要提取 `localStorage.token` 作为 API 认证

## 方法对比

| 方法 | 状态 | 说明 |
|------|------|------|
| `browser_console` (JS) | ❌ 失败 | SecurityError: localStorage access denied（aliyundrive.com 用iframe沙盒）|
| MCP chrome 工具 | ❌ 不可用 | 端口12306连接失败，扩展未激活 |
| **Playwright CDP** | ✅ 成功 | 直连 9333 端口，绕过iframe限制 |

## Playwright CDP 提取步骤

```python
import asyncio, json
from playwright.async_api import async_playwright

async def get():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9333")
        ctx = browser.contexts[0]
        page = await ctx.new_page()
        await page.goto("https://www.aliyundrive.com/")
        await page.wait_for_timeout(3000)
        raw = await page.evaluate("() => localStorage.getItem('token')")
        if not raw:
            return None
        return json.loads(raw)

t = asyncio.run(get())
if t:
    from datetime import datetime, timezone
    exp = datetime.fromisoformat(t["expire_time"].replace("Z","+00:00"))
    now = datetime.now(timezone.utc)
    print(f"用户: {t.get('nick_name')}")
    print(f"过期: {t['expire_time']}")
    print(f"状态: {'过期 ❌' if exp < now else f'有效 ✅ 剩余{(exp-now).seconds}秒'}")
else:
    print("未登录，请重新登录")
```

## 关键参数（从token解析）

```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "5d8291...48d3",
  "expire_time": "2026-05-30T16:32:48Z",
  "user_id": "0ecf4cd0b8504791be61659d6d517e05",
  "default_drive_id": "34265212",
  "default_sbox_drive_id": "44265212"
}
```

## token过期机制

- `access_token`：有效期2小时，过期后需重新登录获取
- `refresh_token`：有效期30天，但**无法通过API刷新**，过期必须重新扫码登录
- `expire_time` 已过 → 直接认过期，需要重新登录

## 重新登录的正确姿势（重要！）

如果用户在Chrome已登录状态下再次"登录"阿里云盘，**不会重新颁发新token**——Chrome会直接复用旧的 `localStorage.token`，`expire_time` 保持不变，和登录前一样。

正确操作：
1. 先**登出**（在阿里云盘网页点用户头像→退出登录），或清除 `localStorage.token`
2. 再重新扫码/账号密码登录
3. 登录后立刻读取token验证 `expire_time` 是否更新

**验证方法**：读token后检查 `expire_time` 是否是未来的时间。如果和之前一样说明登录没有刷新token，需要重来。

## 验证脚本

`~/.hermes/scripts/get_aliyun_token.py`：
```python
import asyncio, json
from playwright.async_api import async_playwright

async def get():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9333")
        ctx = browser.contexts[0]
        page = await ctx.new_page()
        await page.goto("https://www.aliyundrive.com/")
        await page.wait_for_timeout(3000)
        raw = await page.evaluate("() => localStorage.getItem('token')")
        if not raw:
            return None
        return json.loads(raw)

t = asyncio.run(get())
if t:
    from datetime import datetime, timezone
    exp = datetime.fromisoformat(t["expire_time"].replace("Z","+00:00"))
    now = datetime.now(timezone.utc)
    print(f"用户: {t.get('nick_name')}")
    print(f"过期: {t['expire_time']}")
    print(f"状态: {'过期 ❌' if exp < now else f'有效 ✅ 剩余{(exp-now).seconds}秒'}")
else:
    print("未登录，请重新登录")
```