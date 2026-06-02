#!/usr/bin/env python3
"""
hermes_cdp_bot.py — CDP直连真实Chrome操作AI网站
用法: python3 hermes_cdp_bot.py [站点名]
示例: python3 hermes_cdp_bot.py deepseek

依赖: pip install websockets
CDP端口: 9333 (chrome-debug profile) 或 9222 (用户真实Chrome)
"""
import json, asyncio, websockets, urllib.request, sys

# 可用站点配置
SITES = {
    "deepseek": "https://chat.deepseek.com/",
    "doubao":   "https://www.doubao.com/chat",
    "gpt":      "https://chatgpt.com/",
    "gemini":   "https://gemini.google.com/",
    "glm":      "https://chatglm.cn/main/alltoolsdetail?lang=zh",
    "grok":     "https://grok.com/z",
}

CDP_PORT = 9333  # 默认chrome-debug端口

def get_tab_id(site_key=None, url=None):
    """通过HTTP API找到对应tab的完整ID"""
    with urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json", timeout=5) as f:
        tabs = json.load(f)
    for t in tabs:
        if t.get("type") != "page":
            continue
        if site_key:
            if site_key in t.get("url", "").lower():
                return t["id"], t.get("webSocketDebuggerUrl", "")
        if url:
            if url in t.get("url", ""):
                return t["id"], t.get("webSocketDebuggerUrl", "")
    return None, None

async def cdp_send(ws, method, params=None, msg_id=1):
    msg = {"id": msg_id, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    resp = await ws.recv()
    return json.loads(resp)

def get_interactive_elements(nodes):
    """从AX树提取可交互元素"""
    elements = []
    for n in nodes:
        role = n.get("role", {}).get("value", "")
        name = n.get("name", {}).get("value", "")
        bid = n.get("backendDOMNodeId", "")
        if role in ["textbox", "button", "link", "radio", "checkbox"] and name:
            elements.append(f"[{role:<10}] '{name[:60]}' #id={bid}")
    return elements

async def interact_with_site(site_key, question=None):
    """向指定AI网站发送问题并尝试读取回复"""
    url = SITES.get(site_key.lower())
    if not url:
        print(f"未知站点: {site_key}，可用: {list(SITES.keys())}")
        return

    tab_id, ws_url = get_tab_id(site_key=site_key)
    if not tab_id:
        print(f"❌ 未找到 {site_key} 标签页，请先在Chrome中打开")
        return

    if not ws_url:
        ws_url = f"ws://localhost:{CDP_PORT}/devtools/page/{tab_id}"

    question = question or "请用3句话说清楚你是谁"

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        # 1. 导航到目标站
        print(f"→ 导航到 {url}...")
        await cdp_send(ws, "Page.navigate", {"url": url}, msg_id=1)
        await asyncio.sleep(4)

        # 2. 读AX树
        print("→ 读取页面结构...")
        ax = await cdp_send(ws, "Accessibility.getFullAXTree", {"depth": 20}, msg_id=2)
        nodes = ax.get("result", {}).get("nodes", [])
        elements = get_interactive_elements(nodes)

        print(f"可交互元素 ({len(elements)}个):")
        for e in elements[:20]:
            print(f"  {e}")

        has_input = any("textbox" in e for e in elements)
        print(f"\n{'✅ 已登录' if has_input else '❌ 未登录（需先在Chrome中登录）'}")

        if not has_input:
            return

        # 3. 填入问题
        print(f"\n→ 发送: {question}")
        await cdp_send(ws, "Runtime.evaluate", {
            "expression": f"""
            (function() {{
                const ta = document.querySelector('textarea');
                if (!ta) return 'NO TEXTAREA';
                ta.focus();
                ta.value = '{question}';
                ta.dispatchEvent(new Event('input', {{bubbles:true}}));
                return 'OK: ' + ta.value;
            }})()
            """,
            "returnByValue": True
        }, msg_id=3)

        await asyncio.sleep(0.3)

        # 4. 按Enter发送
        await cdp_send(ws, "Runtime.evaluate", {
            "expression": """
            (function() {
                const ta = document.querySelector('textarea');
                if (!ta) return;
                ta.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',keyCode:13,bubbles:true}));
                return 'ENTER SENT';
            })()
            """,
            "returnByValue": True
        }, msg_id=4)

        print("→ 等待回复（8秒）...")
        await asyncio.sleep(8)

        # 5. 尝试读回复（Shadow DOM限制，结果可能为空）
        print("\n=== 读取回复尝试 ===")
        r = await cdp_send(ws, "Runtime.evaluate", {
            "expression": """
            () => {
                const texts = [];
                try {
                    for (let el of document.querySelectorAll('*')) {
                        if (el.shadowRoot) {
                            for (let s of el.shadowRoot.querySelectorAll('span, p, div')) {
                                const t = s.innerText?.trim();
                                if (t && t.length > 5 && t.length < 500) texts.push(t);
                            }
                        }
                    }
                } catch(e) {}
                return { count: texts.length, samples: texts.slice(-5) };
            }
            """,
            "returnByValue": True
        }, msg_id=5)

        result = r.get("result", {}).get("result", {}).get("value", {})
        if isinstance(result, dict):
            print(f"Shadow DOM文本块: {result.get('count', 0)}")
            for t in result.get("samples", []):
                print(f"  → {t[:100]}")
            if result.get("count", 0) == 0:
                print("⚠️ AI回复在Shadow DOM中，CDP无法读取")
                print("💡 建议：直接调厂商API获取回复")

        print("\n✅ 完成")

def list_sites():
    """列出可用站点"""
    print("可用站点:")
    for k, v in SITES.items():
        print(f"  {k:<10} → {v}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        list_sites()
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "list":
        list_sites()
    elif cmd in SITES:
        asyncio.run(interact_with_site(cmd))
    else:
        print(f"未知命令: {cmd}")
        list_sites()