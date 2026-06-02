#!/usr/bin/env python3
"""
diagnose_button_misidentification.py
====================================

诊断"发送按钮误识别"问题。这是反应堆 v2 最常见的 bug:
> 周期2:  CLICK (960, 437) '开启新对话 / 今天 / Mac Mini...'
> (点错了侧边栏按钮,而不是真发送按钮)

用法:
    python3 diagnose_button_misidentification.py deepseek
    python3 diagnose_button_misidentification.py --tab-id 9500172557FFD5EE04AFFC54B7BE4E99

输出:
    - 所有候选"发送"按钮 (按严格匹配 vs 模糊匹配分类)
    - 警告: 模糊匹配命中 div/textarea 容器
    - 推荐修复: 严格匹配 + 按宽度排序

依赖: Python 3.8+, Chrome debug port 9333
"""
import asyncio, json, websockets, urllib.request, sys, argparse

# 严重级别标签
WARN_CONTAINER = "⚠️  CONTAINER"     # 误识别高风险
WARN_NESTED = "⚠️  NESTED"             # 子元素合并文本
WARN_LARGE = "⚠️  TOO_LARGE"           # 按钮过宽 (200px+)
GOOD = "✅ CANDIDATE"                  # 可用候选


async def diagnose(tab_match: str, tab_id: str = None):
    # 找 tab
    if tab_id:
        target_tab_id = tab_id
        target_title = "(specified by --tab-id)"
    else:
        tabs = json.loads(urllib.request.urlopen("http://localhost:9333/json").read())
        target_tab_id = None
        target_title = None
        for t in tabs:
            if t.get("type") == "page" and tab_match in (t.get("title", "") + t.get("url", "")).lower():
                target_tab_id = t.get("id")
                target_title = t.get("title", "")
                break
        if not target_tab_id:
            print(f"❌ 找不到 tab 匹配: {tab_match}")
            print(f"   可用 tabs: {[t.get('title', '') for t in tabs if t.get('type') == 'page']}")
            return False

    print(f"🔍 诊断 tab: {target_title or target_tab_id[:30]}")
    print(f"   ID: {target_tab_id[:40]}")
    print("=" * 70)

    # 连接 WS
    ws_url = f"ws://localhost:9333/devtools/page/{target_tab_id}"
    ws = await websockets.connect(ws_url, max_size=50 * 1024 * 1024)
    msg_id = [0]

    async def cdp(method, params=None):
        msg_id[0] += 1
        await ws.send(json.dumps({"id": msg_id[0], "method": method, "params": params or {}}))
        while True:
            data = json.loads(await ws.recv())
            if data.get("id") == msg_id[0]:
                return data

    # 核心诊断: 抓所有候选"发送"按钮
    r = await cdp("Runtime.evaluate", {
        "expression": """
        (() => {
            const allMatches = [];
            const strictMatches = [];

            for (const b of document.querySelectorAll('button, [role=button], div, span')) {
                const t = (b.innerText || b.textContent || '').trim();
                if (!t) continue;
                if (b.offsetParent === null) continue;  // 不可见

                const rect = b.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;

                const tag = b.tagName;
                const cls = (b.className || '').toString().substring(0, 50);

                // 模糊匹配 (危险)
                if (t.includes('发送') || t.includes('Send') || t.toLowerCase().includes('send')) {
                    allMatches.push({
                        tag, text: t.substring(0, 50), x: Math.round(rect.left + rect.width/2),
                        y: Math.round(rect.top + rect.height/2), w: Math.round(rect.width),
                        h: Math.round(rect.height), cls, len: t.length
                    });
                }
                // 严格匹配 (安全)
                if (t === '发送' || t === 'Send' || t === '提交') {
                    strictMatches.push({
                        tag, text: t, x: Math.round(rect.left + rect.width/2),
                        y: Math.round(rect.top + rect.height/2), w: Math.round(rect.width),
                        h: Math.round(rect.height), cls, len: t.length
                    });
                }
            }
            return {allMatches, strictMatches};
        })()
        """,
        "returnByValue": True
    })

    result = r.get("result", {}).get("result", {}).get("value", {})
    all_matches = result.get("allMatches", [])
    strict_matches = result.get("strictMatches", [])

    # === 报告 ===
    print(f"\n📊 模糊匹配 (dangerous): {len(all_matches)} 个")
    print("-" * 70)
    for m in all_matches:
        severity = GOOD
        if m['len'] > 10:
            severity = WARN_NESTED
        if m['w'] > 200:
            severity = WARN_LARGE
        if m['tag'] in ('DIV', 'SPAN'):
            severity = WARN_CONTAINER
        print(f"  {severity:18s} <{m['tag']:6s}> w={m['w']:3d} '{m['text'][:30]}' @ ({m['x']}, {m['y']})")

    print(f"\n📊 严格匹配 (safe): {len(strict_matches)} 个")
    print("-" * 70)
    if not strict_matches:
        print("  ❌ 严格匹配 0 个 — Enter 兜底必须启用")
    else:
        for m in strict_matches:
            print(f"  {GOOD:18s} <{m['tag']:6s}> w={m['w']:3d} '{m['text']}' @ ({m['x']}, {m['y']})")

    # === 诊断结论 ===
    print("\n" + "=" * 70)
    print("🩺 诊断结论")
    print("=" * 70)

    issues = []
    if len(all_matches) > len(strict_matches) * 2:
        issues.append(f"❌ 模糊匹配数 ({len(all_matches)}) 远大于严格匹配数 ({len(strict_matches)})")
        issues.append("   → 必须用严格匹配 === 而非 .includes()")

    for m in all_matches:
        if m['len'] > 10 and ('发送' in m['text'] or 'Send' in m['text']):
            issues.append(f"⚠️  长文本含'发送': '{m['text'][:30]}' (len={m['len']})")
            issues.append(f"   这是 div 容器的合并文本,不是真按钮")

    if not strict_matches:
        issues.append("⚠️  无严格匹配 — 必须启用 Enter 兜底发送")

    if not issues:
        print("✅ 严格匹配与模糊匹配数差异不大,无明显误识别风险")
    else:
        print("发现以下问题:")
        for i in issues:
            print(f"  {i}")

    print("\n💡 推荐修复 (反应堆 v2 Act 层):")
    print("""
    # 错误 ❌
    if (t.includes('发送')) { click(b) }

    # 正确 ✅
    if (t === '发送' || t === 'Send' || t === '提交') {
        candidates.push({...});
    }
    candidates.sort((a, b) => a.w - b.w);  // 选最小的
    return candidates[0] || null;            // null → Enter 兜底
    """)

    await ws.close()
    return len(issues) == 0


def main():
    parser = argparse.ArgumentParser(description="诊断反应堆 v2 按钮误识别问题")
    parser.add_argument("tab_match", nargs="?", default="deepseek", help="tab title/url 匹配关键字")
    parser.add_argument("--tab-id", help="直接指定 tab ID")
    args = parser.parse_args()

    ok = asyncio.run(diagnose(args.tab_match, args.tab_id))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
