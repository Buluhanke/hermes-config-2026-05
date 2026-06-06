---
name: web-agent-os
description: Web Agent OS — 目标约束型 Web Navigation Agent 架构。目标约束层+WorldGraph+UCB1+真人化+持久记忆。
version: 1.0.0
---

# Web Agent OS v1

## 核心：7组件目标约束架构

```
GoalController → WorldGraph → StateEmbedding
                              ↓
ConstrainedUCB1 → HumanizationLayer → Verifier → MemorySystem
```

## 数据流

```
observe() → encode_state() → GoalController.filter() → UCB1.select()
  → humanize() → execute() → verify() → update(world_graph+memory)
```

## 组件

1. **GoalController** — 三层过滤：SafetyFilter / GoalMask / DepthGuard
2. **WorldGraph** — (state, action) → next_state 图结构
3. **StateEmbedding** — MD5(标题+链接数+元素摘要) 跨页面泛化
4. **ConstrainedUCB1** — UCB1 × GoalMask，未访问动作返回 inf
5. **HumanizationLayer** — 双峰延迟+scroll+hesitation
6. **Verifier** — URL变化/DOM变化/元素消失三重验证
7. **MemorySystem** — 跨session持久化

## 文件

- `~/hermes_web_agent_os.py` — 完整30KB可运行版本（单文件，7组件全内置）
- `~/hermes_v3_demo/` — 工程化项目（多模块，fake_site测试环境，可直接在主机终端运行）
- `references/tool-inventory-check.md` — 68工具分类核查记录（快速验证命令）
- `references/ai-website-login-status.md` — AI网站登录访问模式（豆包/ChatGLM/DeepSeek/Gemini/ChatGPT/Grok登录态现状+解决方案）
- `references/cdp-dom-limitations-2026-06-02.md` — Shadow DOM/CDP DOM限制完整诊断（含Shadow DOM站点清单+替代方案）
- `references/verified-cdp-ws-agent-test.md` — CDP WebSocket连接测试记录
- `references/architecture-20260601.md` — 浏览器架构确认记录（2026-06-01验证：9222用户Chrome已达最优，307元素Accessibility Tree可用）
## 运行

```bash
# 单文件版
python3 ~/hermes_web_agent_os.py 5   # 单次5步
python3 ~/hermes_web_agent_os.py --daemon  # 持续运行

# 工程化demo版（推荐）
cd ~/hermes_v3_demo
python3 start_demo.py --goal 登录 --goal 加入购物车
```

## 已解决：CDP WebSocket 接入方案

**问题**：execute_code 沙盒与主机 Chrome CDP 端口（9333）网络隔离，Playwright connect_over_cdp 也有 bug（context.pages 为空）。

**解法**：不通过 Playwright，直接用 websockets 连接 `ws://127.0.0.1:9333`，由 Hermes Agent 工具层在 host 上下文执行。`dom_tools.py` 已注册为内置工具。

```python
# 复用已有 Chrome 登录态的正确方式
BROWSER_CDP_URL=ws://127.0.0.1:9333  # 不修改 config.yaml，用环境变量
```

### 相关工具
- `dom_tools.py`（`~/.hermes/hermes-agent/tools/`）— 生产级注册工具：`dom_snapshot`、`dom_click`、`dom_fill`、`dom_tabs`
- 详见 `dom-js-inject` skill

## 工具优先级（最新 2026-06）
## 搜索后端：ddgs 优先，SearXNG 降级

**2026-06-02 验证：SearXNG 公开实例（Searx.be / searx.party）全部失效（403/429），ddgs 为可用且稳定的备选。**

`config.yaml` 配置：
```yaml
web:
  backend: ddgs        # ✅ 已验证可用，稳定
  search_backend: ddgs
extract_backend: ddgs
```

**ddgs 优势：**
- Python 包 `ddgs` 已装在 hermes venv，无需外部实例
- 通过 DuckDuckGo 搜索，无 429 限流
- 不依赖 Docker / 本地服务
- 延迟低，响应快

**若 ddgs 不可用（包丢失）：**
```bash
/Users/aimac/.hermes/hermes-agent/venv/bin/pip install ddgs
```

**搜索后端优先级（2026-06-02 确认）：**
```
ddgs > anysearch > searxng（公网实例均已不可用）
```

**⚠️ 不要依赖 SearXNG 公网实例** — 公开实例脆弱，无 SLA，随时可能 403/429/下线。本地 Docker 部署是唯一可靠方案，但占用资源。

---

## 工具优先级（最新 2026-06）

❌ **旧路径（已废弃）：** 截图 → VLM识别 → 找按钮/输入框（慢、贵、Token消耗大）
✅ **正确路径：**
```
第一步：web_extract / browser_get_web_content (直接拿文本)
        ↓ 快（文本）、准（结构化）

第二步：CDP DOM.getDocument (读取DOM结构)
        ↓ 比Accessibility Tree更稳定

第三步：只有以下情况才截图/VLM：
        - Canvas验证码图片
        - 复杂图表
        - 动态渲染无法用文本提取时
```

**2026-06-03 新增：Playwright `press_sequentially` 作为通用输入策略**
- `loc.click()` + `loc.press_sequentially(text, delay=50)` 触发 OS 级 keydown/keyup/input 事件链
- 在 ChatGPT(ProseMirror)/豆包(SyncInputEngine)/Grok(Tiptap) 上全部验证通过
- 适合 Playwright 独立 Chromium（无登录态），速度快，延迟 50ms/字
- 对于需要复用已登录 Chrome 的场景，仍用 `browser_cdp` 工具 + `Input.insertText`

**⚠️ 致命陷阱（2026-06-02 用户直接纠正）：不要默认用截图！** 用户原话："你方向都不对了，为什么浏览器需要截图去识别"。正确的真人化行为：收到任务后先想用什么工具最轻量，而不是默认最先进的工具。截图/VLM是最后手段，不是第一选择。

**原则：永远优先用网页文本提取，而不是截图识别。**

### AI网站已登录状态访问（核心场景）

用户Chrome已登录AI网站时，**必须用`computer_use`控制用户真实Chrome**，而不是开新browser实例：

```
computer_use(action="capture", app="Chrome", mode="ax")
     ↓
读取AX Tree，找到对应标签页元素
     ↓
computer_use(action="click", element=N)  控制已登录的Chrome
```

**browser工具Chrome（agent-browser）≠ 用户Chrome。** agent-browser是独立临时实例，没有AI网站登录态。

### `computer_use` vs `browser_*` 工具 决策树

```
任务需要读网页内容？
├── 用户Chrome已打开该页面 且 已登录
│   └── 用 computer_use 控制用户Chrome（读已登录状态）
├── 需要主动开新页面/新标签
│   └── 用 browser_navigate（独立Chromium实例）
└── 两者都要
    └── 先 computer_use 确认用户Chrome状态，再 browser_navigate 打开新页面
```

### 扁平化 Accessibility Tree + Playwright 语义定位

**顶级Agent（如Browser Use、Agent-E）的核心架构：**

```python
# 扁平化AX Tree：单层列表，模型直接读
# 每个节点带语义标签（role、name、value）
page.get_by_role("button", name="登录")
page.get_by_label("搜索框")
page.get_by_text("提交")
```

**优势：**
- 嵌套AX Tree要"爬树"，扁平化直接读
- Playwright语义定位比XPath/CSS更稳（页面结构变了一般不坏）

---

## 已知限制

1. subprocess超时：在sandbox环境不要用subprocess跑完整agent，直接terminal跑或execute_code内联测试。
2. **CDP Target 生命周期**：Chrome 每次 Page.navigate 后旧的 DevTools target 可能被 detach。`/json` 返回 0 targets ≠ Chrome 关闭（可能是所有标签页都关了），导航后 target ID 会更新。
3. **Hermes 工具 + Python Agent 的正确架构**：多步 agent 循环中，用 Hermes `browser_navigate`/`browser_snapshot` 控制浏览器（工具层在 host 上下文），Agent 逻辑写在独立 Python 脚本里用 `terminal` 或直接在 host 终端跑。不要在 execute_code 里做跨多 CDP call 的长循环。
4. **浏览器 snapshot 可能为空**：即使页面已加载，`browser_snapshot` 有时返回空列表（Chrome 渲染尚未完成）。bridge.py 已带重试。
