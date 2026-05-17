# agent-browser-runtime — Anti-Bot Browser Runtime for AI Agents

**Source**: https://github.com/energypantry/agent-browser-runtime
**License**: Polyform NonCommercial (Docker Compose managed)

## 核心价值

为 AI Agent 提供**共享真实 Chrome 运行时**，包含完整的反爬指纹规避和拟人化操作层。

## 架构

```
Broker (Node.js/Fastify + WebSocket)
    ↓ JSON-RPC
Chrome Extension (Manifest V3)
    ↓ CDP
Chrome Runtime (Chromium + Xvfb + noVNC)
    ↓
TLS Gateway (Go/uTLS JA3对齐)
```

## 反爬指纹层（最可直接借鉴）

### JS 可见面补丁 (`stealth-content.js`)

在页面 JS 上下文中注入以下属性：

| 属性 | 原始值 | 伪装后 |
|------|--------|--------|
| `navigator.webdriver` | `true` | `undefined` |
| `navigator.languages` | `["en-US"]` | `["zh-CN", "zh", "en"]` |
| `navigator.language` | 浏览器语言 | 从种子一致生成 |
| `navigator.platform` | `Linux x86_64` | `MacIntel` / `Win32` |
| `navigator.hardwareConcurrency` | 实际核心数 | 4 或 8（固定） |
| `navigator.deviceMemory` | 实际内存 | 4 或 8（GB） |
| `navigator.maxTouchPoints` | 0 | 0（桌面）或 5（触屏） |
| Canvas `toDataURL` | 真实指纹 | 加随机噪声 |
| AudioBuffer `getChannelData` | 真实指纹 | 加随机噪声 |
| WebGL vendor/renderer | 真实GPU | 从种子映射到已知组合 |

### CDP Header 覆盖（导航前应用）

```javascript
// Network.setExtraHTTPHeaders — 自定义HTTP头
// Network.setUserAgentOverride — UA覆盖
// Emulation.setTimezoneOverride — 时区
// Emulation.setLocaleOverride — 语言
```

**关键**：所有参数从同一个种子生成，保证一致性（UA ↔ CH-UA ↔ Accept-Language ↔ 时区 ↔ WebGL 全部关联）。

## 平台冷却策略

内置高摩擦平台延迟（检测到登录态丢失时触发）：

| 平台 | 冷却时间 |
|------|----------|
| LinkedIn | 180s |
| Instagram | 240s |
| Facebook | 120s |
| Reddit | 60s |

## 拟人化操作原语

### 鼠标轨迹（贝塞尔曲线）

```javascript
// 生成自然弯曲鼠标路径，而非直线
function curvePoints(start, end, { curvature = 0.4 } = {}) {
  const dx = end.x - start.x
  const dy = end.y - start.y
  const cx1 = start.x + dx * curvature + randomOffset()
  const cy1 = start.y + randomOffset()
  const cx2 = end.x - dx * curvature + randomOffset()
  const cy2 = end.y + randomOffset()
  return bezier(start, {x: cx1, y: cy1}, {x: cx2, y: cy2}, end)
}
```

### 动作分层

| 动作 | 描述 |
|------|------|
| `ui.move` | 贝塞尔曲线鼠标移动 |
| `ui.click` | 可配置按住时长 + 按钮 + 点击次数 |
| `ui.type` | 逐字输入，随机延迟 |
| `ui.press` | Key down/up 事件 |
| `ui.scroll` | wheel 分段 + 段间停顿 |
| `ui.waitFor` | 轮询 selector 或文本出现 |

### Ghost Move vs Real Move

- `ghostMove`：分发 synthetic `mousemove` 事件更新悬停状态，但不移动真实光标
- `realMouseMove`：通过 CDP `Input.dispatchMouseEvent` 移动真实光标

## TLS Gateway (Go/uTLS)

JA3 指纹对齐的 HTTPS 代理：

```go
// 默认 JA3 profile: Chrome-124-macOS
// uTLS 库自动生成符合浏览器指纹的 TLS ClientHello
```

## Hermes 可借鉴点

1. **指纹一致性生成**：所有浏览器参数从种子关联生成，不各自独立随机
2. **贝塞尔鼠标曲线**：替代直线移动，更难被检测
3. **平台冷却策略**：对高频访问平台加入退避延迟
4. **Canvas/Audio 噪声注入**：每次调用加随机扰动

## Hermes 现状

macOS 原生 CUA 工具暂不涉及 Docker 部署模式，但指纹一致性思路可直接借鉴到 Hermès 的 stealth 策略。

## 撤销记录

2026-05-17 分析存档，未直接采用（Docker 部署模型与 Hermes 不匹配）。
