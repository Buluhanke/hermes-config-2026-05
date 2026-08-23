# Hermes 浏览器超能力调研成果（2026-08-17）

> 来源：GitHub星标 + 全网搜索验证，browser-use/browser-harness 实地测试

## 当前已验证可用

| 组件 | 状态 | 验证结果 |
|------|------|---------|
| browser-use CLI | ✅ | Chrome连接正常，CDP导航/截图/交互全通 |
| browser-harness | ✅ | 同上，底层CLI |
| cua-driver | ✅ | Hermes内置，macOS背景控制 |
| 本地Chrome | ✅ | chrome://inspect 开启 |

```bash
browser-use doctor
# ✅ chrome running, daemon alive, 1 connection
```

## GitHub Top工具星标榜

| # | 工具 | Stars | 核心能力 | 落地优先级 |
|---|------|-------|---------|-----------|
| 1 | browser-use | 109K | SOTA浏览器Agent，DOM+CDP+LLM | ⭐⭐⭐⭐⭐ |
| 2 | awesome-hermes-agent | 5.3K | 353个技能插件索引 | ⭐⭐⭐⭐ |
| 3 | hermes-agent-self-evolution | 5K | DSPy+GEPA自动优化skills | ⭐⭐⭐⭐⭐ |
| 4 | awesome-hermes-skills | 412 | 79内置+114选配+160社区技能 | ⭐⭐⭐⭐ |
| 5 | MCP (官方内置) | 官方 | 100+服务器连接 | ⭐⭐⭐⭐⭐ |
| 6 | camofox | 社区 | Firefox抗检测+持久化登录态 | ⭐⭐⭐⭐ |
| 7 | firecrawl | 集成 | 实时搜索+抓取+browser渲染 | ⭐⭐⭐⭐ |
| 8 | browserbase | 云服务 | 云浏览器+反爬+住宅代理 | ⭐⭐⭐ |
| 9 | cua-driver (内置) | 官方 | 背景桌面控制 | ⭐⭐⭐⭐⭐ |
| 10 | async-delegate | 40+ | 后台子agent不阻塞 | ⭐⭐⭐ |

## 下一步安装路径（按效果/工作量排序）

### 1. Camofox（持久化浏览器身份）
```bash
git clone https://gh-proxy.com/https://github.com/jo-inc/camofox-browser.git ~/projects/camofox-browser
cd ~/projects/camofox-browser && npm install
# 启动：node server.js (默认端口9377)
# 配置 ~/.hermes/config.yaml:
# browser:
#   camofox:
#     managed_persistence: true
```
效果：Cookie跨运行保留，每个Hermes Profile映射独立浏览器身份。

### 2. hermes-agent-self-evolution（自动优化skills）
```bash
git clone https://github.com/NousResearch/hermes-agent-self-evolution.git ~/projects/hermes-agent-self-evolution
cd ~/projects/hermes-agent-self-evolution
pip install -e ".[dev]"
# 使用：
python -m evolution.skills.evolve_skill --skill github-code-review --iterations 10
```
效果：DSPy+GEPA自动提升skills质量，零GPU训练，~$2-10/次优化。

### 3. async-delegate plugin（后台并行任务）
```bash
git clone https://github.com/kaishi00/hermes-community-plugins.git ~/projects/hermes-community-plugins
cp -r ~/projects/hermes-community-plugins/async-delegate ~/.hermes/plugins/
```
效果：后台子agent执行，主对话继续不阻塞。

### 4. browser-use cloud（反检测+住宅代理）
```bash
browser-use auth login
# 或
printf '%s' "$BROWSER_USE_API_KEY" | browser-use auth login --api-key-stdin
```
效果：云端浏览器，抗检测，195+国家住宅代理。

## 超越真人的关键技术

### cotomi Act（真正超越人类）
- **论文**：arXiv 2605.03231
- **成绩**：WebArena 80.4% > 人类基线78.2%
- **机制**：
  1. 行为观测：被动学用户浏览习惯 → 结构化知识
  2. Shared Knowledge Workspace：人+Agent共同编辑
  3. Adaptive Lazy Observation：只在必要时观察页面
  4. 方向：Agent从"执行者"变"懂你的同事"

### 超人性能差距
```
真人瓶颈：5-10秒/操作，记忆碎片，单线程，注意力分散
Agent优势：0延迟，完美记忆，并行任务，24/7，零干扰
```

## 四层架构

```
┌─────────────────────────────────────┐
│ Layer 4: self-evolution            │ ← DSPy+GEPA自动提升skills
├─────────────────────────────────────┤
│ Layer 3: async-delegate            │ ← 后台子agent，多任务同时跑
├─────────────────────────────────────┤
│ Layer 2: Camofox                   │ ← 抗检测+持久化身份
├─────────────────────────────────────┤
│ Layer 1: browser-use + cua-driver  │ ← CDP网页 + 桌面原生控制
└─────────────────────────────────────┘
```

## 关键链接

- browser-use GitHub: https://github.com/browser-use/browser-use
- browser-harness: https://github.com/browser-use/browser-harness
- Camofox: https://github.com/jo-inc/camofox-browser
- hermes-agent-self-evolution: https://github.com/NousResearch/hermes-agent-self-evolution
- awesome-hermes-agent: https://github.com/0xNyk/awesome-hermes-agent
- cotomi Act: https://arxiv.org/html/2605.03231v1
