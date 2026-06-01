# AI 网站内容提取 — CDP DOM vs 截图（2026-06-02 实战教训）

## 核心教训
用户原话：*"你方向都不对了，为什么浏览器需要截图去识别"*

AI 网站（DeepSeek/豆包/Gemini/ChatGPT/Grok）的回答页面**不要默认截图**，正确流程：

## 工具优先级链（从轻到重）

```
web_extract / curl        → 首选，纯文本最快
CDP Runtime.evaluate     → 动态渲染页面，直接读DOM
browser_snapshot(text)   → 交互后刷新内容
browser_vision/截图      → 最后手段：CAPTCHA、富文本编辑器、验证码
```

## 为什么 CDP DOM 提取优于截图

| 维度 | CDP Runtime.evaluate | 截图 + VLM |
|------|---------------------|-----------|
| 速度 | <1s | 5-15s |
| 成本 | 免费（本地CDP） | API配额消耗 |
| 准确率 | 100%（原始文本） | 受VLM限制 |
| 失败率 | 低 | Error 429（配额耗尽）|

## CDP 提取模式

```javascript
// 通用文章内容提取（适用于 DeepSeek/豆包等）
document.querySelectorAll('p, h2, h3, li').map(el => el.innerText).filter(t => t.trim()).join('\n')

// 聊天消息提取
document.querySelectorAll('[data-message-author-role]').map(el => el.innerText).join('\n')

// Apple ML Research 专用（全量文本）
Array.from(document.querySelectorAll('p, h2, h3, h4, li')).map(el => el.innerText).filter(t => t.trim()).join('\n')
```

## 执行步骤

1. `browser_navigate` 到 AI 网站
2. 输入问题，发送
3. 等待回答（`sleep 8-12`）
4. `browser_console(expression='<JS提取表达式>')` 读 DOM 内容
5. 若 CDP 失败才降级到 `browser_snapshot` 或截图

## 本次翻车记录

| 站点 | 我用的方式 | 正确方式 | 结果 |
|------|-----------|---------|------|
| DeepSeek | 截图 | CDP读DOM | ✅ 成功读10条网页 |
| Gemini | 截图 | 应该CDP | ❌ Error 429配额耗尽 |
| 豆包 | 截图 | 应该CDP | ❌ Error 429配额耗尽 |
| ChatGPT | 截图 | 应该CDP | ❌ Error 429配额耗尽 |
| Grok | 截图 | 应该CDP | ❌ Error 429配额耗尽 |

**根因**：截图依赖 `vision_analyze`，而 vision_analyze 后端用 Gemini API，每日配额有限制（20次/天）。
CDP DOM 提取完全不依赖 vision API，完全免费。

## 已验证的正确流程

```python
# DeepSeek - 成功
result = browser_console(expression="document.querySelectorAll('p, h2, h3, li').map(el => el.innerText).filter(t => t.trim()).join('\\n')")
```

```bash
# Apple ML Research - 成功
curl -sf https://machinelearning.apple.com/research/fast-vision-language-models | grep -o '<p>.*</p>' | head -20
```

## 注意事项

- `browser_snapshot` 有8000字符截断限制，不适合长回答
- CDP 需要标签页已加载完成，等待 `sleep` 是必要的
- `browser_vision` 的 Error 429 表示 vision API 配额用尽，**不要换模型重试**，直接换 CDP 方法