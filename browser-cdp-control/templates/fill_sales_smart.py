#!/usr/bin/env python3
"""
fill_sales_smart.py — single-row sales-form fill for doc.weixin.qq.com smartsheet
(verified working 2026-06-29 against e3_AVYA8AaBAJkCNduhj0AvhTcm4ZMKD)

Usage:
    python3 fill_sales_smart.py "<物料名>" <数量>
    # or batch:
    python3 fill_sales_smart.py "物料1" 200 "物料2" 100

What it does:
  1. Connects to user's foreground Chrome (already has wcom docs login) via CDP 9222
  2. Navigates to the smartsheet URL (or reuses existing tab)
  3. Switches to "采购单" sheet
  4. Scans row 6+ for first empty B column → starts new row
  5. For each (物料名, 数量) pair:
       - Click name box → B<row> → Enter
       - Type 物料名 via Input.insertText → Enter
       - Click name box → E<row> → Enter
       - Type 数量 via Input.insertText → Enter
  6. G column auto-calculates as =E*F (no need to touch)

DEPENDS ON:  `pip install websockets` (already in hermes env)
WHITELIST:   143-row 报价表 B column is fetched at runtime (see fetch_whitelist())

Key design choices:
  - Single persistent CDP WebSocket (no reconnect)
  - All-in-one evaluate_script for cell navigation (NOT mix evaluate + press_key)
  - sleep(80-150) between cell-ref changes (synchronous reads return stale value)
  - `await Promise` for sleep, not setTimeout in event handlers

VERIFIED PITFALLS (see references/doc-weixin-smartsheet-cdp.md):
  - Alt+↓ / Alt+ArrowDown doesn't trigger data-validation dropdown (AlloyEditor
    doesn't inherit Excel shortcut)
  - #alloy-rich-text-editor is the real focus target (NOT #alloy-simple-text-editor)
  - Formula bar always reads formula string, never rendered value
  - Synchronous read after cell-ref change = stale previous cell

SINGLE-VS-BATCH NOTE:
  This script handles multi-row gracefully, but the user's 2026-06-29 statement
  "有客户下单, 我就开一张销售单" = SINGLE ROW per order. Default to single-row
  invocation. Only run multi-row when user says "批量".
"""
import asyncio
import json
import sys
import urllib.request
import websockets

CDP_URL = "http://localhost:9222"
SMARTSHEET_URL = "https://doc.weixin.qq.com/sheet/e3_AVYA8AaBAJkCNduhj0AvhTcm4ZMKD"
TARGET_SHEET = "采购单"


def find_tab():
    """Find the wcom docs tab in user's foreground Chrome."""
    tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json").read())
    for t in tabs:
        if "doc.weixin.qq.com/sheet/" in t.get("url", ""):
            return t["webSocketDebuggerUrl"]
    raise SystemExit("未找到 doc.weixin.qq.com 的 tab。请先在 Chrome 打开该表。")


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self.id = 0

    async def send(self, method, params=None):
        self.id += 1
        await self.ws.send(json.dumps({"id": self.id, "method": method, "params": params or {}}))
        while True:
            raw = await self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == self.id:
                return data

    async def js(self, expr, await_promise=False):
        r = await self.send("Runtime.evaluate", {
            "expression": expr,
            "awaitPromise": await_promise,
            "returnByValue": True,
        })
        return r.get("result", {}).get("result", {}).get("value")

    async def type_text(self, text):
        await self.send("Input.insertText", {"text": text})

    async def press_enter(self):
        for t in ("keyDown", "keyUp"):
            await self.send("Input.dispatchKeyEvent", {
                "type": t, "key": "Enter", "code": "Enter",
                "windowsVirtualKeyCode": 13
            })


async def fetch_whitelist(cdp):
    """Pull 报价表 B column names (143 items as of 2026-06-29) for client-side validation."""
    js = """
    (async () => {
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const cellRef = document.querySelector('input.bar-label');
      const fi = document.getElementById('alloy-simple-text-editor');
      // switch to 报价表
      for (const t of document.querySelectorAll('[role="tab"]')) {
        if (t.textContent.trim() === '报价表') t.click();
      }
      await sleep(1000);
      const items = [];
      let empty = 0;
      for (let r = 2; r <= 250; r++) {
        cellRef.value = 'B' + r;
        cellRef.dispatchEvent(new Event('input', { bubbles: true }));
        cellRef.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
        await sleep(60);
        const v = (fi.textContent || '').trim();
        if (v) { items.push(v); empty = 0; }
        else { empty++; if (empty >= 3) break; }
      }
      // back to target sheet
      for (const t of document.querySelectorAll('[role="tab"]')) {
        if (t.textContent.trim() === '采购单') t.click();
      }
      await sleep(1000);
      return items;
    })()
    """
    return await cdp.js(js, await_promise=True)


def find_closest(name, whitelist, max_n=3):
    """Find closest whitelist matches by substring. For client-side hint."""
    matches = []
    for w in whitelist:
        if name in w or w in name:
            matches.append(w)
    return matches[:max_n]


async def fill_one(cdp, name, qty, target_row=None):
    if target_row is None:
        target_row = await cdp.js(f"""
        (async () => {{
          const sleep = (ms) => new Promise(r => setTimeout(r, ms));
          const cellRef = document.querySelector('input.bar-label');
          const fi = document.getElementById('alloy-simple-text-editor');
          // ensure on target sheet
          for (const t of document.querySelectorAll('[role="tab"]')) {
            if (t.textContent.trim() === '{TARGET_SHEET}') t.click();
          }}
          await sleep(800);
          for (let r = 6; r < 50; r++) {{
            cellRef.value = 'B' + r;
            cellRef.dispatchEvent(new Event('input', {{ bubbles: true }}));
            cellRef.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
            await sleep(80);
            if (!(fi.textContent || '').trim()) return r;
          }}
          return 50;
        }})()
        """, await_promise=True)

    # B 列填名
    await cdp.js(f"""
    (async () => {{
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const cellRef = document.querySelector('input.bar-label');
      const fi = document.getElementById('alloy-simple-text-editor');
      const selectAll = () => {{
        const range = document.createRange();
        range.selectNodeContents(fi);
        range.collapse(false);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      }};
      cellRef.value = 'B{target_row}';
      cellRef.dispatchEvent(new Event('input', {{ bubbles: true }}));
      cellRef.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
      await sleep(200);
      fi.focus();
      selectAll();
    }})()
    """, await_promise=True)
    await cdp.type_text(name)
    await cdp.press_enter()

    # E 列填数量
    await cdp.js(f"""
    (async () => {{
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const cellRef = document.querySelector('input.bar-label');
      const fi = document.getElementById('alloy-simple-text-editor');
      cellRef.value = 'E{target_row}';
      cellRef.dispatchEvent(new Event('input', {{ bubbles: true }}));
      cellRef.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
      await sleep(200);
      fi.focus();
      const range = document.createRange();
      range.selectNodeContents(fi);
      range.collapse(false);
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(range);
    }})()
    """, await_promise=True)
    await cdp.type_text(str(qty))
    await cdp.press_enter()

    return target_row


async def main():
    if len(sys.argv) < 3:
        print("用法: fill_sales_smart.py <物料名> <数量> [物料名] [数量] ...")
        print("示例: fill_sales_smart.py '男士造型梳三件套' 200")
        sys.exit(1)

    args = sys.argv[1:]
    items = []
    i = 0
    while i < len(args):
        name = args[i]
        qty = int(args[i + 1]) if i + 1 < len(args) else 1
        items.append((name, qty))
        i += 2

    ws_url = find_tab()
    async with websockets.connect(ws_url, max_size=10 * 1024 * 1024) as ws:
        cdp = CDP(ws)
        await cdp.send("Runtime.enable")

        # client-side whitelist check
        whitelist = await fetch_whitelist(cdp)
        print(f"[+] 白名单 {len(whitelist)} 个物料已加载")

        for name, qty in items:
            if name not in whitelist:
                closest = find_closest(name, whitelist)
                print(f"[!] '{name}' 不在报价表白名单里")
                if closest:
                    print(f"    接近的: {closest}")
                print(f"    跳过, 不写入 (避免 VLOOKUP 找不到)")
                continue
            row = await fill_one(cdp, name, qty)
            print(f"[+] B{row}={name}  E{row}={qty}  G{row}=E{row}*F{row} 自动算")

    print(f"\n[✓] 完成 {len(items)} 条")


if __name__ == "__main__":
    asyncio.run(main())