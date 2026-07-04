# agent-reach 8/13 渠道真实状态 (2026-06-27 装机实测)

## ✅ 装好即用 (8/13 渠道)

| 渠道 | 状态 | 工具 | 实测延迟 | 备注 |
|---|---|---|---|---|
| **GitHub** | ✅ 完整可用 | `gh` CLI | 200ms | 读取/搜索/Fork/Issue/PR 全包 |
| **YouTube 视频/字幕** | ✅ 可用 | yt-dlp | 500ms | 字幕 + 视频信息（YouTube 限速 429 时 fetch_transcript fallback） |
| **V2EX** | ✅ 公开 API | 直接 HTTP | 300ms | 热门主题/节点浏览/主题详情/用户信息 |
| **RSS/Atom** | ✅ 可用 | feedparser | 100ms | 标准 RSS/Atom 源直读 |
| **全网语义搜索** | ✅ 免费 | Exa via MCP | 1-2s | 无需 API Key，0 费用 |
| **任意网页** | ✅ Jina Reader | curl r.jina.ai/URL | 1s | 免费 200/天，WeChat/部分中文站不支持 |
| **Twitter/X** | ✅ 可选 | twitter-cli | 500ms | 读单条/搜索/时间线/长文（需 Cookie 登录） |
| **B 站** | ✅ 可选 | bili-cli | 500ms | 搜索/热门/详情/音频（无需登录，字幕需 OpenCLI） |

## ⚠️ 已装但需配置 (5/13 渠道)

| 渠道 | 需要什么 | 备注 |
|---|---|---|
| **Reddit** | rdt-cli + Cookie 或 OpenCLI 浏览器登录 | 匿名端点 403 |
| **小红书** | OpenCLI 浏览器登录 (Mac) 或 xiaohongshu-mcp QR 扫描 | 必需登录 |
| **小宇宙播客** | Whisper API key | 音频转文字（免费 key 即可） |
| **雪球股票** | 0 配置但需装 | 自动集成 |
| **LinkedIn** | Jina Reader 公开页 | profile/公司/职位 需登录 |

## 🛠️ 安装命令

```bash
# 一键装
agent-reach install --env=auto

# 加装 5/13 渠道
agent-reach install --channels=reddit,xiaohongshu,linkedin,xiaoyuzhou,xueqiu

# 全装
agent-reach install --channels=all
```

## 📊 体检命令

```bash
source ~/.agent-reach-venv/bin/activate
agent-reach doctor
# 返: 8/13 渠道可用 / 5/13 需配置
```

## 🔁 升级机制 (2026-06 yt-dlp 案例)

yt-dlp 被 B 站反爬时 → agent-reach 自动切换到 bili-cli → 用户**零感知**。

**这是 agent-reach 核心价值**: 不需要你追各种 CLI 的更新，**它替你做选择**。

## 🚨 真实限制

- **每个渠道背后是 CLI 工具** → 跟 CLI 同步更新（不是 SaaS 实时）
- **B 站字幕**需 OpenCLI（macOS 客户端）→ 仍未完美支持
- **小红书**仍需人工登录一次 → 不会自动绕过滑块

## 触发词

"agent-reach 状态 / 哪个渠道能用 / B 站怎么抓 / Twitter 怎么读 / V2EX / RSS / 全网搜索" → 0 思考走 `agent-reach doctor`