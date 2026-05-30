#!/opt/homebrew/bin/python3
"""
Aliyun Drive token 读取与验证脚本
用法: python3 get_aliyun_token.py
依赖: pip install playwright && playwright install chromium
"""
import asyncio
import json
import sys

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
    exp = datetime.fromisoformat(t["expire_time"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    status = "过期 ❌" if exp < now else f"有效 ✅ 剩余{(exp-now).seconds}秒"
    print(f"用户: {t.get('nick_name')} ({t.get('user_name')})")
    print(f"过期: {t['expire_time']}")
    print(f"状态: {status}")
    sys.exit(0 if exp > now else 1)
else:
    print("未登录，请重新登录阿里云盘")
    sys.exit(2)