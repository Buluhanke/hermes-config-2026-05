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

## 已知限制

1. subprocess超时：在sandbox环境不要用subprocess跑完整agent，直接terminal跑或execute_code内联测试。
2. **CDP Target 生命周期**：Chrome 每次 Page.navigate 后旧的 DevTools target 可能被 detach。`/json` 返回 0 targets ≠ Chrome 关闭（可能是所有标签页都关了），导航后 target ID 会更新。
3. **Hermes 工具 + Python Agent 的正确架构**：多步 agent 循环中，用 Hermes `browser_navigate`/`browser_snapshot` 控制浏览器（工具层在 host 上下文），Agent 逻辑写在独立 Python 脚本里用 `terminal` 或直接在 host 终端跑。不要在 execute_code 里做跨多 CDP call 的长循环。
4. **浏览器 snapshot 可能为空**：即使页面已加载，`browser_snapshot` 有时返回空列表（Chrome 渲染尚未完成）。bridge.py 已带重试。
