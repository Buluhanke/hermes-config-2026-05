# web-access (eze-is) 分析存档

**仓库**: https://github.com/eze-is/web-access  
**定位**: Claude Code/Cursor/Codex 等 Agent 的外部 Skill，赋予联网+浏览器自动化能力  
**对比**: Hermes 用内置 Python 实现做同样的事——web-access 是外部 Skill 方案

---

## 核心能力

| 能力 | 实现方式 |
|------|---------|
| CDP Proxy | Node.js HTTP API (`cdp-proxy.mjs`)，连接本地 Chrome/Edge，端口 3456 |
| `/eval` | 在页面执行 JS，读 DOM、提数据、填表单 |
| `/click` | JS `el.click()`，快速，触发懒加载 |
| `/clickAt` | CDP `Input.dispatchMouseEvent`，真实鼠标事件，能触发文件对话框 |
| `find-url.mjs` | 读本地 Chrome/Edge 书签/历史，按关键词检索 |
| 站点经验积累 | 按域名存储操作经验到 `references/site-patterns/` |
| 并行分治 | 多目标分发子 Agent，共享一个 Proxy |

---

## 关键技术细节

### TCP 端口检测（不用 WebSocket）
```javascript
// browser-discovery.mjs
// 用 TCP connect 检测端口，避免触发浏览器授权弹窗
const socket = net.createConnection(port, '127.0.0.1');
```

### 浏览器 Pin 机制
首次连接成功后固定浏览器 ID，重连时只接受同一 ID，防止漂移到其他浏览器。

### URL 通过 POST body 传输（v2.5.3+）
```
# 旧写法（?url= 会截断含 & 的 URL）
GET /new?url=https://xhs.com/explore?xsec_token=ABC&type=normal
# 新写法（POST body 不存在分隔符歧义）
POST /new + body: 'https://xhs.com/explore?xsec_token=ABC&type=normal'
```

### 三层联网工具选择策略
1. **WebSearch** — 搜索摘要、发现信息来源
2. **WebFetch / curl** — URL 已知，定向提取
3. **浏览器 CDP** — 登录态、交互操作、动态渲染页面（小红书/微信公众号等）

---

## 浏览哲学（值得借鉴）

> 目标驱动，而非步骤驱动。

1. **明确目标** — 定义"什么算完成了"，作为后续所有判断的锚点
2. **选择起点** — 选最可能直达的方式一次验证，不成功则调整
3. **过程校验** — 每一步的结果是证据，不只是成功/失败的二元信号
4. **完成判断** — 对照任务成功标准，不为"完整"浪费代价

---

## Hermes 可吸收的部分

**高价值（可实现）**：
- `find-url.mjs` Python 版 — 读 Chrome 书签/历史，按关键词找之前访问过的 1688 供应商页面
- 站点经验积累 — 轻量 JSON 存储，按域名记录 1688 平台特征和已知坑

**不需要**：
- Node.js HTTP Proxy 架构（我们的 `mcp-chrome-stdio` 更简洁）
- Browser Pin / 不擅自降级（我们的 CDP 稳定性已有其他方案）

---

## 架构对比

| 维度 | web-access | Hermes |
|------|------------|--------|
| 实现方式 | 外部 Skill（Node.js） | 内置（Python） |
| 依赖 | Node.js 22+ | Chrome 已开 remote-debugging |
| 连接方式 | HTTP Proxy（端口 3456） | stdio / CDP 直连 |
| 登录态 | 携带用户浏览器登录态 | 同 |
| 并行 | 子 Agent 多 tab | mcp-chrome-stdio 多工具 |
