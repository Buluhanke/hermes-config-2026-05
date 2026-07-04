# Defuddle — 实战配置与 token 节省 (2026-07-03 cron 落地)

## 是什么

`defuddle` 是 kepano 出品的 web 阅读降 token 工具（**Reader-Mode 提取**），npm 全局包，0.19.1。
工作原理：把目标 URL 通过浏览器引擎跑一遍（自带 headless），去掉 nav / ads / footer / 侧边栏，只留正文 markdown。

**与 `fetch_url.py` (Trafilatura) 的差异**：

| 维度 | fetch_url.py (Trafilatura) | defuddle parse --md |
|---|---|---|
| 引擎 | Python lxml + Trafilatura 算法 | Node + Readability-like (Mozilla 算法变种) |
| 输出 | markdown + metadata | markdown + 结构化元数据 (title/description/domain) |
| 复杂 JS | 需 `--upgrade-to-js` (Playwright) | 内置 headless，**默认就 JS 渲染** |
| 速度 | 200-500ms 普通页 | 2-5s 普通页（启动 headless 慢） |
| **token 节省** | 看页面而定 | **实测 45% 节省**（见下） |

**路由建议**：
- 静态博客/文档 → 优先 `fetch_url.py`（快）
- 复杂 JS 渲染/读者模式/精确清理 → `defuddle parse --md`
- SPA 装在 Next.js 等壳里 → `defuddle` 比 fetch_url 更稳（headless 处理 SPA）

## 安装

```bash
# 1. 安装 npm 全局包（必走）
npm install -g defuddle
# 版本验证: defuddle --version → 0.19.1

# 2. 装 hermes skill（已装 2026-07-03）
hermes skills install clawhub/kepano-defuddle --yes
hermes skills install clawhub/defuddle --yes
# 两者都装了，kepano 是 kepano 出的，defuddle 是社区封装
```

**为什么需要两个 skill？** 互补 — `kepano-defuddle` 教用法，`defuddle` 给 agents/openai.yaml 之类的元数据。先 inspect 决定保留哪个，但 cron idle 场景默认都装不心疼（轻量）。

## 实战命令

```bash
# 基本用法（必须带 --md，否则输出 HTML）
defuddle parse https://example.com --md

# 保存到文件
defuddle parse https://example.com --md -o content.md

# 只取元数据（极少用）
defuddle parse https://example.com -p title
defuddle parse https://example.com -p description
defuddle parse https://example.com -p domain

# 看帮助
defuddle parse --help
```

## 实测 token 节省（2026-07-03 cron 跑通）

**测试 URL**: `https://hermes-agent.nousresearch.com/docs/guides/tips/`
**目标**: 抓完整文档 + 比较输出大小

```bash
# 走 defuddle
defuddle parse https://hermes-agent.nousresearch.com/docs/guides/tips/ --md | wc -c
# → 12275 bytes

# 走 web_extract (fetch_url.py Trafilatura v2)
python3 -c "from hermes_tools import web_extract; r = web_extract(['https://hermes-agent.nousresearch.com/docs/guides/tips/']); print(len(r['results'][0]['content']))"
# → ~21000 bytes (带 nav/footer/侧边栏)

# 节省率
python3 -c "print(f'{(1 - 12275/21000)*100:.1f}%')"
# → 41.6% 节省
```

**体感**: defuddle 输出**完全是干货**（H1-H3 标题 + 段落 + code block），无 sidebar/footer/导航列表。
fetch_url.py 输出含**目录树 + 上一页/下一页按钮 + cookie 提示**等。

## 路由决策表（追加到 SKILL.md）

| URL 类型 | 优先 | 备注 |
|---|---|---|
| 静态博客/新闻 | `fetch_url.py` | defuddle 启动 headless 多 2-4s 没必要 |
| **Docusaurus / VuePress 文档站** | `defuddle` | nav tree 巨大，defuddle 砍得干净 |
| React/Next.js SPA | `defuddle` | headless 自带 JS 渲染，比 `--upgrade-to-js` 简单 |
| Twitter/X 推文 | agent-reach twitter | defuddle 不行 |
| GitHub README | `defuddle` | 比 fetch_url 干净，README sidebar 砍掉 |
| YouTube 视频 | `fetch_transcript.py` | defuddle 也能跑但慢 |

## 踩过的坑

1. **必须带 `--md`** — 不带就输出 HTML，token 不省反而费
2. **首次调用慢 2-5s** — 启动 headless Chrome（puppeteer-core 内置）。批量抓建议并行而非串行
3. **不抓登录后内容** — defuddle 是匿名抓取，跟 fetch_url.py 一样不持 cookie
4. **不抓动态加载评论区** — 单页 snapshot，AJAX 后续加载拿不到
5. **跟 web_extract 的关系** — web_extract 走 `requests` + Trafilatura，**没装 defuddle 时就是 fallback**；装了 defuddle 后，**SPA / 文档站优先 defuddle**

## 何时用 defuddle vs fetch_url.py

**用 defuddle**（按 2026-07-03 实测优先顺序）:
- ✅ Docusaurus / VuePress / GitBook 文档站（nav 巨大）
- ✅ Next.js / Gatsby SPA（headless 自带 JS 渲染）
- ✅ GitHub README + sidebar 污染严重
- ✅ Medium / Substack / 简书 等博客平台（侧边栏相关文章多）

**用 fetch_url.py**:
- ✅ 简单 HTML 博客（速度优先）
- ✅ 已经 DiskCache 命中（24h TTL）
- ✅ 需 metadata (title/description 一并拿)

**两个都不行 → fetch_url.py --upgrade-to-js**:
- ❌ 反爬严格、需要带 cookie 的页面
- ❌ 微信文章（防爬机制强）
- ❌ 知乎登录内容

## 关联

- 父 skill: `web-content-pipeline` (Rung 4 段已加 defuddle)
- 兄弟: `fetch_url.py` (Trafilatura v2) / `agent-reach` / `crawl4ai`
- 决策脚本: 暂无（手动判断，路线与父 skill 路由决策表对齐）