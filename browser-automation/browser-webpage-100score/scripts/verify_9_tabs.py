"""
9 站 tab 实地验证脚本
- 不能只看 curl /json 的 title 字符串
- 必须用 Runtime.evaluate 抓 document.body.innerText 验证渲染

用法:
  python3 verify_9_tabs.py
  python3 verify_9_tabs.py --site gemini  # 单站

黄金流程步骤 5 (见 SKILL.md "必读" 段)
"""
import json, urllib.request, asyncio, websockets, re, argparse

SITES = [
    ("Gemini",   "gemini.google"),
    ("Doubao",   "doubao.com"),
    ("ChatGLM",  "chatglm"),
    ("DeepSeek", "deepseek"),
    ("ChatGPT",  "chatgpt"),
    ("Grok",     "grok"),
    ("Yuanbao",  "yuanbao"),
    ("Wenxin",   "yiyan"),
    ("Tongyi",   r"qianwen|tongyi"),
]

LOGIN_HINTS = ["登录", "Sign in", "sign_in", "登录态", "未登录", "新对话", "新聊天", "新建", "Log in"]

def get_pages():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9333/json").read())
    return [t for t in tabs if t.get('type') == 'page']

def find_ws(pages, kw):
    for t in pages:
        if re.search(kw, t.get('url',''), re.IGNORECASE):
            return t['webSocketDebuggerUrl']
    return None

async def check(ws_url):
    async with websockets.connect(ws_url, max_size=2*1024*1024) as ws:
        await ws.send(json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {
                "expression": """
                (function(){
                    var b = document.body ? document.body.innerText : '';
                    var title = document.title;
                    var url = location.href;
                    var hints = %s;
                    var hasLogin = hints.some(function(k){ return b.indexOf(k) >= 0; });
                    return JSON.stringify({
                        title: title, url: url,
                        bodyLen: b.length,
                        bodySample: b.substring(0, 150).replace(/\\n/g, '|'),
                        hasLogin: hasLogin
                    });
                })()
                """ % json.dumps(LOGIN_HINTS),
                "returnByValue": True
            }
        }))
        r = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
        return json.loads(r.get('result', {}).get('result', {}).get('value', '{}'))

async def main(target=None):
    pages = get_pages()
    print(f"=== 9 站 tab 实地验证 ===\n")
    print(f"  当前 page tab: {len(pages)} 个\n")

    targets = [s for s in SITES if target is None or target.lower() in s[0].lower()]
    for name, kw in targets:
        ws_url = find_ws(pages, kw)
        if not ws_url:
            print(f"  ❌ {name:10s} tab 缺失 (URL 含 '{kw}' 的 page tab 找不到)")
            continue
        try:
            d = await check(ws_url)
        except Exception as e:
            print(f"  ❌ {name:10s} {str(e)[:60]}")
            continue
        title = d.get('title','')[:25]
        bodyLen = d.get('bodyLen', 0)
        hasLogin = d.get('hasLogin', False)
        body = d.get('bodySample','')[:80]
        flag = "✅" if bodyLen > 200 and hasLogin else "⚠️" if bodyLen > 50 else "❌"
        loginMark = "登录✓" if hasLogin else "未登录"
        print(f"  {flag} {name:10s} [{loginMark}] body={bodyLen:5d}字符 标题={title}")
        print(f"        预览: {body[:80]}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", help="单站验证 (例: gemini)")
    args = parser.parse_args()
    asyncio.run(main(args.site))
