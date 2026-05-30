# JS注入打标签DOM解析 — 实测验证 2026-06-02

## 核心原理
在浏览器内通过JS给所有可交互元素打`data-hermes-id`标签，然后用Playwright的`[data-hermes-id='X']`精准定位执行。

## 为什么比XPath/CSS selector更稳
1. **零延迟**：JS毫秒级注入，不依赖Python侧DOM解析
2. **Token节省10x**：提取500 token vs 原始HTML 50000 token
3. **视觉盲区过滤**：getBoundingClientRect()过滤隐藏元素
4. **唯一ID**：避免重名冲突（多个`.btn`时用ID精准区分）

## 实测数据（httpbin.org/forms/post）
```
提取到 13 个元素:
  [ID:1] input type=text
  [ID:2] input type=tel
  [ID:3] input type=email
  [ID:4-6] input type=radio (small/medium/large)
  [ID:7-10] input type=checkbox
  [ID:11] input type=time
  [ID:12] textarea
  [ID:13] button type=submit text=Submit order
fill/click 100%精准
```

## JS脚本
```javascript
() => {
    let elements = document.querySelectorAll('a, button, input, textarea, select, [role="button"], [tabindex="0"]');
    let interactables = [];
    let idCounter = 1;
    elements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0 || el.style.visibility === 'hidden' || el.style.display === 'none') return;
        const uniqueId = idCounter++;
        el.setAttribute('data-hermes-id', uniqueId);
        let text = el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || '';
        interactables.push({
            id: uniqueId,
            tag: el.tagName.toLowerCase(),
            type: el.type || '',
            text: text.trim().substring(0, 60),
            placeholder: el.placeholder || ''
        });
    });
    return interactables;
}
```

## Playwright执行示例
```python
elements = await page.evaluate(JS_EXTRACT_DOM)
# 精准定位执行
await page.locator('[data-hermes-id="12"]').fill('张三')
await page.locator('[data-hermes-id="13"]').click()
```

## 已知限制
- **百度不适用**：百度在headless模式注入验证UI遮挡搜索框，换正常表单网站即可
- **动态内容**：需要等networkidle确保JS渲染完毕
- **iframe**：需跨frame遍历（el.contentDocument查询）

## 脚本位置
主验证脚本：`/Users/aimac/hermes_dom_parser.py`

## 与Vision Agent Loop的关系
- Vision Agent Loop = 截图→VLM→action（适合视觉决策）
- JS打标签 = 高精度DOM定位（适合已知目标元素的精准操作）
- 两者结合：VLM识别目标 → JS标签精准执行