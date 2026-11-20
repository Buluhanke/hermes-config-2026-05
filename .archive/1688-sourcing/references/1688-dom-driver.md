# 1688 DOM 驱动法（本机实测可用，2026-08-19）

computer_use 的 AX 无障碍树**看不到** 1688 的"所在地区→江浙沪"浮层（CSS 浮层不进树），
所以点不到。改用 AppleScript 直接对真实 Chrome 执行 JS。所有片段均在本机会话跑通。

## 0. 读 JS 文件的中文编码（必看，否则乱码）

AppleScript `read as string` 默认按 Mac Roman 读 UTF-8 文件，中文变乱码，
导致 `.click()` 匹配到错误元素（曾误点 11 个含"江浙沪"的商品标题）。
**必须用 `as «class utf8»`**：

```applescript
set js to read (POSIX file "/tmp/foo.js") as «class utf8»
tell application "Google Chrome"
  set active tab index of front window to 1
  set r to execute active tab of front window javascript js
end tell
```

## 1. 搜索栏搜词（⚠️ 必须走页面搜索框，不要 set URL 带 keywords 参数）

**错误做法（曾返工，千万别用）**：`set URL to "https://s.1688.com/s/1688search?keywords=..."`
→ 1688 重定向上清参数成 `offer_search.html`，变空搜，出鞋/工艺品乱品。UTF-8 或 GBK 编码都救不了。

**正确做法（二选一）**：
- 推荐：computer_use 点页面内搜索框 → `type` 中文 → `key return`（见 SKILL.md 方法B）。提交后 URL 带 `spm=...searchbox.0`，搜索框 `.value` 等于搜索词才算成功。
- 兜底 JS（已登录 Chrome 内）：点 `.ali-search-input` 聚焦后用 `document.execCommand('insertText','16*16*16cm纸箱')` 写入再派发回车事件。
  验证：`document.querySelector('.ali-search-input').value === '16*16*16cm纸箱'` 且 `document.title` 含搜索词。

## 2. 展开"所在地区"浮层（hover 懒加载，纯 click() 无效）

`.location-select` 是 hover 懒加载，`el.click()` 不触发加载。必须 dispatch 事件序列：

```javascript
// /tmp/open_loc.js
(() => {
  const sel = document.querySelector('.location-select');
  if (!sel) return JSON.stringify({ err: 'no .location-select' });
  ['mouseenter','mouseover','mousedown','mouseup','click'].forEach(t =>
    sel.dispatchEvent(new MouseEvent(t,{ bubbles:true, cancelable:true, view:window })));
  return JSON.stringify({ dispatched:true, selText: sel.textContent.trim().slice(0,20) });
})();
```
执行后**等 5–8 秒**，`li.areas-list` 才异步加载出来（"所有地区/江浙沪/华东区/华南区/..."）。

## 3. 点"江浙沪"

```javascript
// /tmp/click_jzh.js
(() => {
  const af = document.querySelector('.area-filter');
  if (!af) return JSON.stringify({ err:'no .area-filter' });
  const jzh = [...af.querySelectorAll('li.areas-list')].find(li => li.textContent.trim() === '江浙沪');
  if (!jzh) return JSON.stringify({ err:'no 江浙沪 li' });
  ['mouseenter','mousedown','mouseup','click'].forEach(t =>
    jzh.dispatchEvent(new MouseEvent(t,{ bubbles:true, cancelable:true, view:window })));
  return JSON.stringify({ clicked:true, text:jzh.textContent.trim() });
})();
```
验证：结果页省份变义乌/绍兴/苏州/常州（江浙沪）；混入少量广东属正常。

## 4. 翻页（无标准分页，是无限滚动）

`window.scrollTo(0, document.body.scrollHeight)` 触发"加载更多"，再提取新 offerId。

## 5. 提取 offerId → 构造详情 URL（⚠️ 只取主列表，避开浮窗陷阱）

**错误做法**：全页扫 `?offerId=` 或 `detail.1688.com/offer/` → 会扫到左侧推荐、底部"找相似"浮窗、
旺旺客服 `air.1688.com`、店铺链接，**全是乱品**。

**正确做法**：主列表每个商品卡片自带"找相似"链接，其 `offerIds=` 才是真商品 ID：

```javascript
(() => {
  const ids = new Set();
  document.querySelectorAll('a').forEach(a => {
    const m = a.href.match(/similar_search\.html\?offerIds=(\d+)/);
    if (m) ids.add(m[1]);
  });
  return JSON.stringify([...ids]);
})();
```
真实详情 URL：`https://detail.1688.com/offer/{id}.html`

> 注：主列表是虚拟滚动/懒加载，`.search-offer-wrapper` 直接 children 常只有壳子；
> 滚到底再提取、`similar_search?offerIds=` 链接出现即代表主列表已渲染。
> 不要信 `document.body.innerText`（SPA 异步常仅 ~1900 字符）。

## 6. 详情页核对 16×16×16cm（异步加载，等 4–5s）

```javascript
(() => {
  const t = document.body.innerText;
  const hit = /16[\s*×xX]16[\s*×xX]16\s*cm/i.test(t);
  return JSON.stringify({ hit, url: location.href });
})();
```

## 7. 读用户截图（OCR 通道）

本机 `vision_analyze` 因 Hermes venv 的 PIL 损坏 404。改用：
`env -i /usr/local/bin/python3 ~/.hermes/scripts/baidu_ocr.py <img>`（清环境跑，能读图）。
