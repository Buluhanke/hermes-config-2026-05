---
name: dom-js-inject
description: Chrome CDP JS注入打标签 — 极速DOM提取 + 精准元素定位。通过CDP WebSocket(9333)连接Chrome，在页面内执行JS给所有可见交互元素打data-hermes-id标签，提取极简元素列表(<500 Token)供LLM决策，然后用精确坐标执行click/fill操作。比browser_snapshot更轻量、比VLM截图更快。依赖chrome-debug实例运行于9333端口。
triggers:
  - 需要提取网页可交互元素列表
  - 需要精准点击/输入而不依赖XPath/CSS selector
  - 发现browser_snapshot返回太慢或token消耗太大
  - 想让LLM直接看到带坐标的精简元素描述
---

## 快速使用

```bash
cd ~/.hermes/hermes-dom-extractor
python3 cdp_ws_client.py              # 列出当前Chrome标签页
python3 cdp_ws_client.py <url>         # 提取指定URL的页面元素
```

## Python API

```python
import asyncio
from hermes_dom_extractor.cdp_ws_client import (
    CDPConnection, list_chrome_tabs, dom_tag_and_extract,
    build_hermes_prompt, dom_click_by_id, dom_fill_by_id
)

async def example():
    tabs = list_chrome_tabs()
    tab = next((t for t in tabs if t['url'].startswith('http')), None)

    cdp = CDPConnection(tab['ws_url'], tab['id'])
    await cdp.connect()

    elements, title, url = await dom_tag_and_extract(cdp)
    prompt = build_hermes_prompt(elements, title, url)
    # prompt 示例:
    # 页面标题: 订单表单
    # 页面URL: https://httpbin.org/forms/post
    # 可交互元素 (共 13 个):
    #   [ID:1] input type=text 文本='custname' @(212,29) 153x21
    #   [ID:13] button type=submit 文本='Submit order' @(54,636) 92x21

    # 执行操作
    await dom_fill_by_id(cdp, hermes_id=1, value='张三', elements=elements)
    await dom_click_by_id(cdp, hermes_id=13, elements=elements)

    await cdp.close()

asyncio.run(example())
```

## 核心优势

| 对比项 | DOM提取(本技能) | browser_snapshot |
|--------|----------------|-----------------|
| Token/页 | ~300-500 | ~2000-5000 |
| 推理速度 | <1秒 | 3-8秒 |
| 定位方式 | data-hermes-id+坐标 | @eN ref |
| 适用场景 | 表单/列表/普通网站 | 复杂动态UI/验证码 |

## 工作流程

1. **Observe**: `dom_tag_and_extract()` → JS注入打标签 + 提取精简元素列表
2. **Think**: LLM阅读prompt，决定要操作哪个元素
3. **Act**: `dom_click_by_id()` / `dom_fill_by_id()` 用精确坐标执行
4. **Loop**: 等待页面渲染 → 重复步骤1

## JS标签注入脚本核心逻辑

```javascript
// 给所有可见交互元素打 data-hermes-id
var els = document.querySelectorAll('a[href], button, input, textarea, select...');
els.forEach(el => {
    if (rect.width > 0 && rect.height > 0 && style.display !== 'none') {
        var uid = counter++;
        el.setAttribute('data-hermes-id', uid);
        // 提取描述: tag, type, text, 坐标
    }
});
```

## 已知限制

- 依赖 Chrome CDP 9333(chrome-debug实例)运行
- Chrome内部页面(chrome://)无法通过CDP访问
- 反爬站点(百度等)可能注入隐藏UI → JS已用getBoundingClientRect过滤零尺寸元素
- iframe内元素需分别连接对应frame的target

## 文件位置

- 核心模块: `~/.hermes/hermes-dom-extractor/cdp_ws_client.py`
- 验证脚本: `~/hermes_dom_parser.py` (独立Playwright版)