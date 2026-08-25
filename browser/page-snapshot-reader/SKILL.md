---
name: page-snapshot-reader
description: "browser_navigate+snapshot分层读页免截图。Use when 用Hermes内置浏览器读页面内容"
triggers:
  - "读取这个页面"
  - "读取这个链接"
  - "帮我读这个页面"
  - "read this page"
  - "browser_snapshot"
l1: browser
l2: read
l3: cdp-snapshot
---

# Page Snapshot Reader — CDP Browser 零成本页面读取

## 核心工具

`browser_navigate` + `browser_snapshot` 是 Hermes 内置的 CDP browser 工具链，**零安装、零模型**，直接读 DOM 结构化文本。

## 工作流

```
URL → browser_navigate → browser_snapshot → 返回结构化 AX 树
```

## 使用方式

```python
browser_navigate(url="https://example.com")
browser_snapshot()  # 无需参数，直接拿当前页 AX 树
```

## 成功率经验值

| 页面类型 | 结果 | 说明 |
|---|---|---|
| Wikipedia | ✅ | 表格/标题/数据全有 |
| GitHub | ✅ | 文件列表/commit/目录结构 |
| Hacker News | ✅ | 标题/分数/评论数/作者/时间 |
| 新闻/博客/论坛 | ✅ | 标准 HTML 渲染 |
| StackOverflow | ✅ | 代码块/答案结构完整 |
| 知乎/微信/小红书 | ❌ | 登录墙，内容被遮 |
| Canvas 图表页 | ❌ | Flot/Chart.js 等纯 Canvas 无法读 |
| JS 无限滚动 | ⚠️ | 不稳定，内容懒加载 |

**整体成功率：约 70-80%**

## 何时降级

页面内容明显不完整时，降级到 `browser-read-funnel`（Firecrawl → Scrapling → Crawl4AI → 截图 OCR）。

## 已知限制

- `browser_navigate` 第一次可能超时，重试一次即可
- `browser_snapshot` 大页面会截断，`full=true` 可获取完整内容（但丢失 ref ID）
- `browser_vision` vision 分析依赖 Gemini，当前版本有格式兼容问题

## 验证命令

```bash
browser_navigate(url="https://en.wikipedia.org/wiki/Paris")   # ✅ 表格数据完整
browser_navigate(url="https://github.com/torvalds/linux")   # ✅ 目录/commit 完整
browser_navigate(url="https://news.ycombinator.com")        # ✅ 标题/分数/评论完整
```
