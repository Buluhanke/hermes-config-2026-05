# 企业微信表格 Tab 点击 — 坐标法实战 2026-07-10

## 问题
`browser_click @e13` 在 doc.weixin.qq.com/sheet 上报：
```
Could not locate element with role=link name=报价表
```
原因：tab 是动态渲染的，snapshot 的 element ref 在点击前已失效。

## 解决链路（实测）

### Step 1：找元素坐标
```javascript
var el = Array.from(document.querySelectorAll('*')).find(function(e){return e.textContent.trim()==='报价表'});
var r = el.getBoundingClientRect();
JSON.stringify({text:el.textContent.trim(), x:r.left, y:r.top, w:r.width, h:r.height})
```
输出：`{"text":"报价表","x":286.71875,"y":842,"w":77,"h":29}`

### Step 2：CDP 点击（mousePressed + mouseReleased）
```python
# mousePressed
browser_cdp(method='Input.dispatchMouseEvent', params={
    'type': 'mousePressed', 'button': 'left', 'clickCount': 1,
    'x': 286.7, 'y': 842
})
# mouseReleased
browser_cdp(method='Input.dispatchMouseEvent', params={
    'type': 'mouseReleased', 'button': 'left', 'clickCount': 1,
    'x': 286.7, 'y': 842
})
```

### Step 3：等待切换
```bash
sleep 3
```

## 关键发现

- `textContent.trim()` 匹配中文 tab 名最稳
- 坐标是 viewport 相对坐标（不是文档坐标）
- 点击中心点 = `x + w/2, y + h/2`
- 工作表 tab 在第一个 snapshot 的底部，`[ref=e10]` ~ `[ref=e16]`
- 当前 tab 列表：抖音、5月、采购单、报价表、转换、对账单、报销单

## Tab ref 快速索引（快照内）
```
@e10 = 抖音
@e11 = 5月
@e12 = 采购单
@e13 = 报价表  ← 报错过，改用坐标法
@e14 = 转换
@e15 = 对账单
@e16 = 报销单
```
**注意**：导航后 ref 会变，不能缓存依赖。

## 相关文件
- SKILL.md：browser-cdp-control
- `references/doc-weixin-smartsheet-cdp.md`：完整 AlloyEditor 读写方案
- `templates/fill_sales_smart.py`：销售单填表模板
