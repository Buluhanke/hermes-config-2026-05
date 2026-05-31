# 2026-05-31 空闲学习记录 — 方向C (规划层)

## 背景

Cron 触发 (23:11)。网络：github+hn blocked，HN Firebase API ✅。screen_watcher 进程死亡，成功重启。

## 核心发现

### 1. Cloudflare Turnstile 强制 WebGL 指纹（2026-05-30 起）

来源：HN [62pts] hacktivis.me — 作者使用 webkit-gtk 浏览器时 Turnstile 无限循环

**关键事实**：
- 2026-05-24 起，Cloudflare Turnstile 开始要求 WebGL renderer fingerprint 才能放行
- WebKitGTK 浏览器被整体封禁（WebKit 默认屏蔽 WebGL fingerprinting）
- Firefox 145.0 可通过（privacy.resistfingerprinting 未默认启用）
- Cloudflare 官方回应："Turnstile uses browser fingerprinting to verify you're human. Privacy tools that block or randomize fingerprinting make your browser look like a bot trying to hide its identity."

**与 Hermes CAPTCHA 研究的关联**（补充 CogCAPTCHA30）：
- CogCAPTCHA30 研究检测的是 **行为过程**（决策/记忆/感知/推理维度）
- Turnstile WebGL 检测的是 **设备指纹**（硬件/驱动特征）
- 两条防线独立运行，Hermes chrome-debug 需同时绕过两条
- 防御方向：
  - WebGL spoofing via chrome-debug flags 或 browserbase proxies
  - 注意：Firefox 的 privacy.resistfingerprinting 在某些 Firefox 版本中即使开启也可能被 Turnstile 检测

**对 Hermes auto_execute 的具体影响**：
- DRY_RUN=True 状态下不执行真实浏览，不受影响
- DRY_RUN=False 后如遇到 Turnstile 保护的站点（GitHub、Cloudflare CDN 站点等），可能被拦截
- 需要在测试环境中验证 chrome-debug 能否通过 Turnstile

### 2. Tesla V100 SXM2 家用推理 £200（HN 76pts）

来源：blog.tymscar.com — 作者将 V100 SXM2（2017）通过 £50 适配器装入游戏 PC

**硬件对比（带宽维度）**：
| 硬件 | 显存带宽 | 成本 |
|------|---------|------|
| V100 SXM2 16GB (2017) | **900 GB/s** HBM2 | £200（含适配器） |
| RTX 4080 16GB | 736 GB/s GDDR6X | 已有 |
| M3 Max | 400 GB/s | 整机 |
| M4 Max | 546 GB/s | 整机 |
| M5 Max | 614 GB/s | £3,000+ 整机 |
| RTX 5090 32GB | 1,792 GB/s | £2,000+ |
| RX 7900 XTX 24GB | 960 GB/s | £700+ |

**关键洞察**：
- 推理瓶颈是 memory bandwidth，非 FLOPS（验证 idle_learning 前期 Kog AI 结论）
- 2017 年 datacenter GPU 在推理带宽上仍领先所有 Mac
- llama.cpp 的 tensor splitting 可跨两张 GPU 运行（4080+V100）
- 27B 参数模型 @ 32 tok/s，总成本仅 £200
- **32GB 双卡方案**：V100 16GB + RTX 4080 16GB = 32GB VRAM，成本远低于单一 RTX 5090

**对 Hermes（M4 24GB）的意义**：
- 不对标——Mac mini 无法装 dGPU，但验证了 memory bandwidth 是核心限制
- 为未来推理性能提升提供硬件路线图参考
- llama.cpp 在 Mac 上同样受带宽限制，近期优化空间有限

### 3. The Website Specification — Agent Readiness 规范（HN 314pts）

来源：specification.website — Joost de Valk，128 topics

**项目概况**：
- 平台无关的网站技术规范，覆盖 10 大分类
- Foundations / SEO / Accessibility / Security / Well-Known URIs / **Agent Readiness** / Performance / Privacy / Resilience / Internationalisation
- **Agent Readiness 共 18 项**（3 Required，其余 Recommended/Optional）
- 开源（MIT），MCP 服务器可用，每页 Markdown 可访问

**Agent Readiness 18 项关键规范**：

| 规范 | 等级 | 描述 |
|------|------|------|
| Stable URLs | Required | URL 是公开合约，变更会破坏引用 |
| Agent readiness（总纲） | Recommended | 稳定URL+结构化数据+干净语义+robots控制 |
| `/llms.txt` | Recommended | 站点根目录 Markdown 索引，LLM 友好 |
| Per-page Markdown endpoints | Recommended | 每页 .md 源或 content negotiation |
| robots.txt for AI crawlers | Recommended | 命名 AI user-agent 并显式允许/禁止 |
| Structured data for agents | Recommended | JSON-LD + schema.org 给 agent 类型化事实 |
| Machine-readable formats | Recommended | JSON/RSS/Markdown 端点替代 HTML |
| HTTP Link headers for discovery | Recommended | 通过 HTTP header 公告 llms.txt/sitemap/RSS |
| Agent Skills discovery | Recommended | Cloudflare 主导 RFC，well-known URI 发布 agent 技能 |
| `/llms-full.txt` | Optional | 所有页面的完整 Markdown 拼接 |
| Content Signals in robots.txt | Optional | IETF AI 内容权限声明 |
| Web Bot Auth | Optional | RFC 9421 HTTP Message Signatures 验证 bot 身份 |
| MCP and tool discovery | Optional | MCP 服务器发现 |
| A2A agent cards | Optional | `/.well-known/agent-card.json`，Agent-to-Agent 协议 |

**对 Hermes 规划层的价值**：
1. **Agent Skills discovery RFC** — Cloudflare 主导，well-known URI 发布 agent 指令
   - 与 hermes-agent 的 skill 体系天然契合
   - 未来可考虑为 Hermes 注册自身能力到该规范
2. **Web Bot Auth** — RFC 9421 HTTP Message Signatures
   - 可作为 Hermes 向服务端验证身份的标准方式
   - 替代 user-agent 字符串猜测，更可靠
3. **A2A agent cards** — Agent-to-Agent 协议
   - 可作为 Hermes 多 agent 协调（orbiter/worker 架构）的参考
   - JSON-RPC 调用，well-known 发现
4. **MCP server 发现** — Hermes 的 native-mcp client 可消费此规范

## 可执行改进

1. screen_watcher 进程死亡（09:56→23:11，13h+无监控）→ 已重启成功 ✅
2. Cloudflare Turnstile WebGL 验证：后续在某 Turnstile 保护站点的 chrome-debug 测试需做
3. The Website Specification MCP server（`mcp.specification.website`）可集成到 native-mcp 配置
   - 指令：添加 `"specification-website": {"transport": "http", "url": "https://mcp.specification.website/mcp"}` 到 config.yaml

## 下次方向

D — 执行层（auto_execute DRY_RUN=False 前的坐标校准测试）
