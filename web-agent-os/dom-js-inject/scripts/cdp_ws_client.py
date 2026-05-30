#!/usr/bin/env python3
"""
Hermes DOM Extractor — 极简CDP WebSocket方案

直接连接 Chrome CDP (9333)，用 Runtime.evaluate 执行 JS 打标签，
通过 Input.dispatchMouseEvent / dispatchKeyEvent 执行精准操作。

不依赖 Playwright 的 context/page 管理，避免 "Cannot create new page" 错误。

CDP文档: https://chromedevtools.github.io/devtools-protocol/
"""

import asyncio
import json
import urllib.request
from typing import Optional

CDP_HOST = "127.0.0.1"
CDP_PORT = 9333


# ============================================================================
# JS 注入脚本
# ============================================================================

JS_TAG_AND_EXTRACT = r"""
(() => {
    var selectors = 'a[href], button, input, textarea, select, [role="button"], [role="link"], [tabindex="0"], [contenteditable="true"]';
    var els = document.querySelectorAll(selectors);
    var result = [];
    var counter = 1;

    els.forEach(function(el) {
        var rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;

        var cStyle = window.getComputedStyle(el);
        if (cStyle.display === 'none' || cStyle.visibility === 'hidden') return;

        var uid = counter++;
        el.setAttribute('data-hermes-id', uid);

        var text = (el.innerText || el.value || el.placeholder ||
                    el.getAttribute('aria-label') || el.name ||
                    el.id || '').trim().substring(0, 80);

        var href = el.href || (el.getAttribute('href') || '').trim().substring(0, 100);

        result.push({
            id: uid,
            tag: el.tagName.toLowerCase(),
            type: el.type || 'unknown',
            name: el.name || '',
            elem_id: el.id || '',
            placeholder: el.placeholder || '',
            text: text,
            href: href,
            x: Math.round(rect.left + rect.width / 2),
            y: Math.round(rect.top + rect.height / 2),
            w: Math.round(rect.width),
            h: Math.round(rect.height)
        });
    });
    return result;
})()
"""


# ============================================================================
# CDP WebSocket 连接管理
# ============================================================================

class CDPConnection:
    def __init__(self, ws_url: str, target_id: str):
        self.ws_url = ws_url
        self.target_id = target_id
        self.ws = None
        self._msg_id = 1
        self._pending = {}
        self._reader_task = None

    async def connect(self):
        import websockets
        self.ws = await websockets.connect(self.ws_url, max_size=10 * 1024 * 1024)
        self._reader_task = asyncio.create_task(self._read_loop())
        return self

    async def _read_loop(self):
        """持续读取 WebSocket 消息，按 id 分发"""
        import websockets
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                mid = msg.get('id')
                if mid and mid in self._pending:
                    self._pending[mid].set_result(msg)
        except (websockets.exceptions.ConnectionClosed, Exception):
            pass

    async def _send(self, method: str, params: dict) -> dict:
        """发送 CDP 命令，等待响应"""
        mid = self._msg_id
        self._msg_id += 1
        future = asyncio.Future()
        self._pending[mid] = future

        await self.ws.send(json.dumps({
            'id': mid,
            'method': method,
            'params': params
        }))

        result = await asyncio.wait_for(future, timeout=20)
        if 'error' in result:
            raise Exception(f"CDP error: {result['error']}")
        return result

    async def eval_js(self, js: str, max_size: int = 10 * 1024 * 1024) -> any:
        """在页面上下文执行 JS，返回结果"""
        result = await self._send('Runtime.evaluate', {
            'expression': js,
            'returnByValue': True,
            'generatePreview': False,
            'awaitPromise': False
        })
        rv = result.get('result', {}).get('result', {})
        if rv.get('type') == 'undefined':
            return None
        if rv.get('type') == 'error':
            raise Exception(f"JS error: {rv.get('description', '')} - {rv.get('value', '')}")
        return rv.get('value')

    async def get_document(self) -> str:
        """获取页面标题"""
        result = await self._send('Runtime.evaluate', {
            'expression': 'document.title',
            'returnByValue': True
        })
        return result.get('result', {}).get('result', {}).get('value', '')

    async def get_url(self) -> str:
        """获取页面URL"""
        result = await self._send('Runtime.evaluate', {
            'expression': 'window.location.href',
            'returnByValue': True
        })
        return result.get('result', {}).get('result', {}).get('value', '')

    async def mouse_click(self, x: int, y: int):
        """模拟鼠标点击（精确坐标）"""
        for step, button, count in [
            ('mousePressed', 'left', 1),
            ('mouseReleased', 'left', 1)
        ]:
            await self._send('Input.dispatchMouseEvent', {
                'type': step,
                'x': x,
                'y': y,
                'button': button,
                'clickCount': count
            })

    async def mouse_move(self, x: int, y: int):
        await self._send('Input.dispatchMouseEvent', {
            'type': 'mouseMoved',
            'x': x,
            'y': y
        })

    async def key_type(self, text: str):
        """输入文本（逐字符）"""
        for char in text:
            # 先 keydown
            await self._send('Input.dispatchKeyEvent', {
                'type': 'keyDown',
                'text': char,
                'key': char,
                'code': f'Key{char.upper()}'
            })
            await self._send('Input.dispatchKeyEvent', {
                'type': 'keyUp',
                'text': char,
                'key': char,
                'code': f'Key{char.upper()}'
            })

    async def key_press(self, key: str):
        """按一个键（如 Enter）"""
        for step in ['keyDown', 'keyUp']:
            await self._send('Input.dispatchKeyEvent', {
                'type': step,
                'key': key,
                'code': key
            })

    async def close(self):
        if self._reader_task:
            self._reader_task.cancel()
        if self.ws:
            await self.ws.close()


# ============================================================================
# 工具函数
# ============================================================================

def list_chrome_tabs() -> list[dict]:
    """获取 Chrome 所有标签页信息"""
    url = f"http://{CDP_HOST}:{CDP_PORT}/json"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        tabs = json.loads(resp.read())
    return [
        {
            'id': t['id'],
            'url': t.get('url', ''),
            'title': t.get('title', ''),
            'ws_url': t['webSocketDebuggerUrl']
        }
        for t in tabs
        if not t.get('url', '').startswith('chrome-extension')  # 过滤扩展页面
    ]


def build_hermes_prompt(elements: list[dict], page_title: str, page_url: str) -> str:
    """构建发给本地 LLM 的精简 Prompt"""
    lines = [
        f"页面标题: {page_title}",
        f"页面URL: {page_url}",
        f"可交互元素 (共 {len(elements)} 个):",
        ""
    ]
    for el in elements:
        pos = f"({el['x']},{el['y']}) {el['w']}x{el['h']}"
        info = f"[ID:{el['id']}] {el['tag']}"
        if el['type'] != 'unknown':
            info += f" type={el['type']}"
        if el.get('placeholder'):
            info += f" placeholder='{el['placeholder']}'"
        if el.get('text'):
            info += f" 文本='{el['text']}'"
        elif el.get('href'):
            info += f" 链接={el['href'][:60]}"
        lines.append(f"  {info} @{pos}")
    return "\n".join(lines)


# ============================================================================
# 核心 API
# ============================================================================

async def dom_tag_and_extract(cdp: CDPConnection) -> tuple[list[dict], str, str]:
    """
    在页面上执行 JS 注入打标签，并提取元素列表。
    返回: (elements, page_title, page_url)
    """
    title, url, elements_raw = await asyncio.gather(
        cdp.get_document(),
        cdp.get_url(),
        cdp.eval_js(JS_TAG_AND_EXTRACT)
    )
    elements = elements_raw if isinstance(elements_raw, list) else []
    return elements, title, url


async def dom_click_by_id(cdp: CDPConnection, hermes_id: int, elements: list[dict]):
    """通过 hermes_id 找到元素的精确坐标，执行点击"""
    for el in elements:
        if el['id'] == hermes_id:
            await cdp.mouse_click(el['x'], el['y'])
            return
    raise ValueError(f"No element with data-hermes-id={hermes_id}")


async def dom_fill_by_id(cdp: CDPConnection, hermes_id: int, value: str, elements: list[dict]):
    """通过 hermes_id 找到输入框，清空后填入文本"""
    for el in elements:
        if el['id'] == hermes_id:
            # 先点击聚焦
            await cdp.mouse_click(el['x'], el['y'])
            await asyncio.sleep(0.05)
            # 全选删除
            await cdp.key_press('Meta+a')
            await asyncio.sleep(0.05)
            await cdp.key_press('Backspace')
            await asyncio.sleep(0.05)
            # 输入文本
            await cdp.key_type(value)
            return
    raise ValueError(f"No element with data-hermes-id={hermes_id}")


# ============================================================================
# 入口
# ============================================================================

async def main(url: str = None):
    """CLI入口：列出标签页或提取指定标签页的元素"""
    tabs = list_chrome_tabs()
    print(f"=== Chrome 标签页 ({len(tabs)} 个) ===")
    for i, t in enumerate(tabs):
        print(f"  [{i}] {t['title'][:50]} | {t['url'][:70]}")

    if not url:
        # 默认选第一个 HTTP 标签页
        http_tabs = [t for t in tabs if t['url'].startswith('http')]
        if not http_tabs:
            print("没有找到 HTTP 标签页")
            return
        t = http_tabs[0]
    else:
        # 按 URL 匹配
        t = next((tab for tab in tabs if tab['url'] == url), None)
        if not t:
            print(f"未找到标签页: {url}")
            return

    print(f"\n连接到: {t['title']}")
    cdp = CDPConnection(t['ws_url'], t['id'])
    await cdp.connect()

    elements, title, page_url = await dom_tag_and_extract(cdp)
    prompt = build_hermes_prompt(elements, title, page_url)

    print(f"\n=== 提取结果 ===")
    print(f"页面: {title}")
    print(f"URL: {page_url}")
    print(f"元素数: {len(elements)}")
    print(f"\n{prompt}")

    # 演示：找到第一个 input 类型元素并输出其 hermes_id
    for el in elements:
        if el['tag'] == 'input' and el['type'] in ['text', 'search']:
            print(f"\n演示: 点击输入框 ID={el['id']} @ ({el['x']},{el['y']})")
            await dom_click_by_id(cdp, el['id'], elements)
            break

    await cdp.close()


if __name__ == '__main__':
    import sys
    target_url = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(target_url))