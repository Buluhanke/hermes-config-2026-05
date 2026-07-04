# doc.weixin.qq.com Smartsheet (企业微信智能表格) — CDP Read/Write 实战 (2026-06-29)

## 适用场景

需要在 Hermes 内部**编程读写**企业微信文档的智能表格 (`doc.weixin.qq.com/sheet/...`)：
- 用户没给 API key / 不是企业管理员 → 走不了官方 OpenAPI
- 表格内容是**敏感数据**（账单/采购单/对账）→ 不能复制到本机 .xlsx
- 浏览器已经登录 → CDP 接管最省事

> 通用结论：和 `docs.qq.com` 腾讯文档**完全不通**。这是企业微信域，OpenAPI 只对企业管理员 + API 模式机器人开放，且机器人只能编辑**自己创建**的文档，别人的表格编辑不了。

## 关键架构事实（2026-06-29 实测）

```
┌─────────────────────────────────────────────┐
│ doc.weixin.qq.com 智能表格                  │
│                                             │
│  [公式栏: A1] [#alloy-simple-text-editor]    │  ← DOM 钩子
│  ┌────────────────────────────────────┐     │
│  │  <canvas>  (0,0)  实际绘制在       │     │
│  │  editor-zone_grid___TyIk           │     │
│  │  {x:0, y:146, w:1920, h:696}       │     │  ← 真实视觉位置
│  │                                    │     │
│  │  单元格内容在 canvas 像素里         │     │  ← DOM 读不到
│  │  没有 data-row / data-col 属性      │     │
│  └────────────────────────────────────┘     │
│  [tab] 抖音 5月 采购单 报价表 转换 对账单 报销单 │  ← 工作表切换
└─────────────────────────────────────────────┘
```

**核心难点**：智能表格的内容是**用 `<canvas>` 绘制的**，**不是 DOM 文本**。`document.querySelectorAll('.cell, [data-row]')` 全部 0 命中。所以：
- ❌ 不能用 DOM textContent 读单元格
- ✅ 但**公式栏 `#alloy-simple-text-editor`** 是标准 `contenteditable=true` 的 div，会显示当前 active cell 的内容 → 这是唯一读/写入口
- ✅ **cell ref 输入框 `input.bar-label`** 可以跳转到任意坐标
- ✅ **底部 `[role="tab"]`** 可以切换工作表

## 实际可用的钩子（实测验证）

| 钩子 | 选择器 | 作用 |
|---|---|---|
| 公式栏（当前 cell 内容） | `#alloy-simple-text-editor` (contenteditable=true) | 读写当前单元格内容 |
| 单元格地址 | `input.bar-label` (A1, B5...) | 跳转到指定 cell |
| 工作表切换 | `[role="tab"]` (文本匹配) | 切「抖音/5月/采购单/...」 |
| 编辑器区域 | `.editor-zone_grid___TyIk` | focus 容器 |

## 读写流程

### 写一个单元格（最稳的方法）

```javascript
// 1. focus name box, 跳到目标 cell
const cellRef = document.querySelector('input.bar-label');
cellRef.focus();
cellRef.value = 'C5';
cellRef.dispatchEvent(new Event('input', { bubbles: true }));
cellRef.dispatchEvent(new KeyboardEvent('keydown', {
  key: 'Enter', bubbles: true, cancelable: true
}));
cellRef.blur();

// 2. 等 ~400ms 让 cell 加载完 (异步渲染, 同步读会拿到旧值!)
await new Promise(r => setTimeout(r, 400));

// 3. focus 公式栏, 清空, 写入新值
const fi = document.getElementById('alloy-simple-text-editor');
fi.focus();
fi.textContent = '';  // 不能用 innerText
fi.textContent = '新内容';

// 4. 触发 input 事件让 React/Vue 同步 state
fi.dispatchEvent(new Event('input', { bubbles: true }));

// 5. 提交 (Enter)
document.dispatchEvent(new KeyboardEvent('keydown', {
  key: 'Enter', bubbles: true, cancelable: true
}));
```

### 读一个单元格

```javascript
// 同样: 先 cell ref 跳转, 等 400ms, 读公式栏
await new Promise(r => setTimeout(r, 400));
const value = document.getElementById('alloy-simple-text-editor').textContent;
```

### 切换工作表

```javascript
const tabs = document.querySelectorAll('[role="tab"]');
for (const t of tabs) {
  if (t.textContent.trim() === '采购单') {  // 严格匹配, 否则可能命中 "开始"/"插入"
    t.click();
    break;
  }
}
// 等 1-2 秒让 sheet 重新渲染
await new Promise(r => setTimeout(r, 1500));
```

## 踩过的坑（实打实测, 不是猜）

### ❌ 坑 1: 同步读公式栏拿到旧值

```javascript
cellRef.value = 'B1';
cellRef.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
cellRef.blur();
const v = fi.textContent;  // ❌ 还是 A1 的值, 渲染是异步的
```

✅ **必须** `await sleep(400)` 再读。第一次踩这个坑时 9 个 cell 全拿到相同值。

### ❌ 坑 2: 用 `evaluate_script` 设 cell ref 后再用 `press_key` 移动 cell

```javascript
// 这样写没用
cellRef.value = 'A1';
cellRef.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
// 之后再调 mcp_chrome_devtools_mcp_press_key 'Tab' → cell ref 不动
```

`mcp_chrome_devtools_mcp_press_key` 用 CDP `Input.dispatchKeyEvent` 真实键入到**当前 focused 元素**。如果 focus 实际在 editor-zone grid 但 React 还在用上一次 cell ref 的 onBlur 处理 → 键入会被吞。

✅ 解决：**全部走 `evaluate_script` 一次性 setTimeout 链**，别混用 CDP press_key + JS cell ref。

### ❌ 坑 3: Tab / ArrowRight 不会移动 active cell

```javascript
document.querySelector('.editor-zone_grid___TyIk').focus();
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab' }));  // ❌ cell ref 不动
```

`mcp_chrome_devtools_mcp_press_key` 的 `Right` 是非法的，要用 `ArrowRight`。但即使合法，cell ref 也不动——智能表格的 active cell 移动是 React 内部的 keydown handler，监听的是 `editor-zone` 内部，不监听 document-level。

✅ **0 思考方案**：放弃 ArrowKey 移动，统一走 cell ref 输入框跳转。

### ❌ 坑 4: `cellRef.value = 'B1'` 没触发 React onChange

React 受控组件不会响应直接赋值。需要：
```javascript
cellRef.dispatchEvent(new Event('input', { bubbles: true }));   // 触发 React onChange
cellRef.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
```

漏掉 `bubbles: true` 也会失败——React 17+ 用事件冒泡。

### ❌ 坑 5: 公式栏写值后没提交

```javascript
fi.focus();
fi.textContent = '新值';
// 完了, 没提交, 表格里 cell 实际没变
```

✅ 必须 `Enter` 提交。公式栏是 `contenteditable` div 但内部是 React state，`textContent` 设进去只是改 DOM，state 没同步，Enter 触发 onKeyDown 才会真正写入 store。

## 完整读取工作表全表数据（参考模板）

```javascript
async () => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const cellRef = document.querySelector('input.bar-label');
  const fi = document.getElementById('alloy-simple-text-editor');
  const result = [];
  
  // 假设已知 6 列 A-F, 扫描 30 行
  for (let row = 1; row <= 30; row++) {
    const rowData = [];
    for (let col = 0; col < 6; col++) {
      const colLetter = String.fromCharCode(65 + col);
      const cellId = `${colLetter}${row}`;
      
      cellRef.focus();
      cellRef.value = cellId;
      cellRef.dispatchEvent(new Event('input', { bubbles: true }));
      cellRef.dispatchEvent(new KeyboardEvent('keydown', {
        key: 'Enter', bubbles: true, cancelable: true
      }));
      cellRef.blur();
      await sleep(150);
      rowData.push(fi.textContent || '');
    }
    // 空行提前终止
    if (rowData.every(v => v === '')) break;
    result.push({ row, data: rowData });
  }
  return result;
};
```

30 行 × 6 列 ≈ 27 秒（每次 150ms 等待）。可优化：去掉 150ms 直接连续写，最后统一 sleep 1000ms + 一次读全部（不可行——公式栏一次只能存一个 cell）。

## 触发词 / 何时用本 skill

- "企业微信表格编辑" / "企微文档自动化" / "doc.weixin.qq.com 写入"
- "智能表格读数据" / "smartsheet CDP"
- "没 API key 怎么改企微表格"
- 用户丢 `doc.weixin.qq.com/sheet/...` 链接要自动化

## 关联 skill

- `browser-cdp-control` (本 skill 父类) — Chrome 9222 端口、登录态继承、CDP 基础
- `hermes-mac-os-agent` — 如果用户说 "直接看到屏幕操作" (本 skill 走 CDP 不需要视觉)

## 已知失败模式（不要重复踩）

1. 混用 `evaluate_script` 设 ref + `mcp_chrome_devtools_mcp_press_key` 移 cell → 100% 失败
2. 同步读公式栏 → 拿到旧值
3. 用 canvas 截图 OCR 读内容 → 既慢又不准, 公式栏直读更可靠
4. 试图调用企业微信 OpenAPI → 大概率没权限, 且只能编辑自己创建的文档
5. 用 `browser_use` 自然语言驱动 → 8B 模型不认 smartsheet 的视觉结构, 容易点错 cell
6. 公式栏回读 → 拿到公式字符串不是渲染值 (永远, AlloyEditor 设计)
7. Alt+↓ / Alt+ArrowDown → AlloyEditor 不响应, 没有下拉弹出 (2026-06-29 实测)

## 真实 active element = `#alloy-rich-text-editor` (2026-06-29)

公式栏 `#alloy-simple-text-editor` 是 **显示** 元素, 不是 **focus** 元素. 真正接收键盘事件的是 `#alloy-rich-text-editor` (AlloyEditor 实例).

**改完 cellRef + sleep(400) 后, 第一件事检查 active element**:
```javascript
return {
  activeId: document.activeElement.id,
  activeTag: document.activeElement.tagName
};
// 期望: { activeId: "alloy-rich-text-editor", activeTag: "DIV" }
// 拿到其他 (BODY, alloy-simple-text-editor...) → 重新走 cell ref
```

**Alt+ArrowDown 在 AlloyEditor 里实测结果 (2026-06-29)**:
- 发给 alloy-rich-text-editor → 0 popup
- 发给 document → 0 popup
- F2 + Alt+ArrowDown 组合 → 0 popup
- 唯一可见反应是 `smart-selection-board` 高亮板出现 (选区蓝边框, 不是下拉)

**结论**: 用户口中的"下拉点选" 在 AlloyEditor smartsheet 里**没有原生 UI**, 用户只是手动习惯了用键盘/鼠标选, 实际数据验证(VLOOKUP) 在后端跑. 我们直接键入物料名 (白名单校验) 达到同样效果.

## 单次 vs 批量的语义侦测 (2026-06-29 用户纠正)

**触发**: 用户说 "我开个单 / 做个表 / 填个东西" / "客户下单我开一张".

**0 思考自检**:
- 含 "开**一张** / 一次 / 一个 / 这条" → 单条模式, **不做批量工具**, 直接交互填, 用户给一条数据跑一次
- 含 "每天 / 批量 / 多个 / 100 条" → 批处理模式, 写脚本
- 没上下文 → **默认单条先 ship**, 一句话告知: "以后要批量我再包装"

**反面教材 (2026-06-29)**: 用户说 "有客户下单, 我就开一张销售单", 我立刻做了 CSV 批量导入工具 + `fill_sales_fast.py` 长脚本. 用户立刻纠正 "不是要批量". 浪费 3 轮 + 长脚本 + **两次误写入真实表格** (row 8 "测试产品 99", row 9 "趣集狗挡风帘 200").

**铁律**: "开一张 / 帮我填一个" 这种语义 = 0 思考走交互填表. **即使心里觉得"以后可能要批量"也等用户说**. 不要提前反向 YAGNI (不要提前批量化).

**Trigger phrases**:
- 单条: "开张 / 一个 / 一次 / 帮我填 / 给我做"
- 批量: "批量 / 每天 / 很多 / 循环 / 自动"
