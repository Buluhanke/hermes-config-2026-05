# cua-driver Daemon 与 MCP 生命周期 — Session 细节 (2026-06-26)

## 核心结论

**`cua-driver` 不是一个进程，是两个**：
- **Daemon** (`com.trycua.driver`, TCC identity 持有者) — 真正拥有 macOS 辅助功能/屏幕录制权限的长驻进程
- **MCP server** (`cua-driver mcp`) — 一个**前台 launcher**，79 秒后退出，作用是 spawn/attach daemon 并 proxy MCP 请求

绝大多数"权限突然没了""capture 返回 0 元素"的故障都是这两个之间的状态错位。

## 我踩过的坑（按发生顺序）

### 坑 1：TCC 权限明明显示 true，capture 还是返回空

```
$ ~/.local/bin/cua-driver permissions status --json
{"accessibility": true, "screen_recording": true, "screen_recording_capturable": true}

# 但 mcp_cua_driver_check_permissions 报：
MCP server 'cua-driver' is not connected
```

**根因**：`permissions status` 报的是 daemon 的 TCC 状态（pid=20936, ppid=1），但 MCP 通道断了，所以任何 `mcp_cua_driver_*` 调用都失败。**两个独立的健康指标，必须分别验证**。

**铁律**：看到 `mcp_cua_driver_*` 任何调用失败时，**不要看 permissions 状态自我安慰**。直接走诊断序列。

### 坑 2：`cua-driver mcp` 在前台跑会自动退出

```bash
$ ~/.local/bin/cua-driver mcp &
# 79 秒后 exit code 0
$ ps aux | grep cua-driver
# 只剩 daemon，mcp launcher 没了
```

**根因**：`mcp` 子命令本身是 proxy launcher，不是 server。它 spawn 出 daemon 后就把 stdin/stdout 转给 daemon proxy，前台跑会因为 MCP 客户端断开（stdin EOF / IPC 断）而退出。

**修法**：用 `open -n -g -a CuaDriver --args serve` 启动 daemon，让它脱离 MCP launcher 独立运行。`--args serve` 等价于 `mcp` 但保持 daemon 一直活着。

### 坑 3：`get_window_state` 必须先传 `window_id`，否则报错

```python
mcp_cua_driver_get_window_state(capture_mode="som", pid=13426)
# → error: Missing required integer field: window_id
```

**修法**：
```python
windows = mcp_cua_driver_list_windows(pid=13426)
# 选 is_on_screen=true 的那个
wid = [w for w in windows if w.get("is_on_screen")][0]["window_id"]
state = mcp_cua_driver_get_window_state(capture_mode="som", pid=13426, window_id=wid)
```

### 坑 4：vision_analyze 直接调永远报 Gemini 400

```
Error: Gemini HTTP 400 (INVALID_ARGUMENT): API key expired.
```

**根因**：`vision_analyze` 直连 Gemini，当前 API key 过期。**不能等修 key，必须绕过**。

**修法**：
```python
import sys; sys.path.insert(0, "/Users/aimac/.hermes/scripts")
from mac_vision_fallback import vision_fallback
r = vision_fallback(image_path="/tmp/screen.png", question="...")
# source: "nv_vision_direct" (5-9s 走 NVIDIA Nemotron-VL)
```

**注意**：CLI 模式（不在 agent 进程）会落 2 级 nv 直连，因为 1 级的 `vision_with_cache.cached_vision_analyze` 依赖 `from tools.vision_tools import vision_analyze_tool` —— 这个 module 不在 CLI 上下文里。

## 完整恢复序列（验证有效）

```bash
# 1. 杀干净
pkill -f "cua-driver" && sleep 2

# 2. 起 daemon (后台, 长驻)
open -n -g -a CuaDriver --args serve
sleep 3

# 3. 验证 daemon 健康 (注意: 是 daemon 的 TCC 身份)
~/.local/bin/cua-driver permissions status --json
# 期望: accessibility=true, screen_recording=true

# 4. MCP 通道 (Hermes 端由 gateway 维护, 如果断了就重新发起)
# 在 Hermes 里就是继续调 mcp_cua_driver_*，gateway 会重连

# 5. 验证 MCP 真能用 (而非只 daemon 健康)
mcp_cua_driver_list_apps  # 看返回 app 列表, 不要 error
```

## MCP 失联症状速查

| 现象 | 真正问题 | 修法 |
|---|---|---|
| `MCP server 'cua-driver' is not connected` | MCP 通道断了 | `pkill` → `open -n -g -a CuaDriver --args serve` → 等 |
| `capture mode=som 0x0 app=...` 元素为空 | daemon 在但 MCP 通道未注册 app | 上面同 |
| `permissions status` 返回 true 但 capture 空 | daemon TCC 健康但 MCP 通道挂了 | 同上 |
| capture 返回非空但 vision_analysis 报 "Gemini 400" | 视觉模型层问题, 跟 cua-driver 无关 | 走 `mac_vision_fallback.vision_fallback` |
| `window_id required` | 没先 list_windows 取 id | 先 `list_windows(pid=N)` 取 `window_id` |
| `mcp_cua_driver_*` 整个 batch 全失败 | daemon 死了 + 没人重启 | 跑 `pkill` + 重启序列 |

## 复盘

- **6 次连续失败**（mcp_cua_driver_check_permissions/get_window_state 都报 "not connected"）是因为我没意识到 `mcp` 是 launcher 不是 server
- **误判**："`permissions status` 说权限正常，所以不是权限问题" — 错，权限是 daemon 层的，capture 是 MCP 层的
- **正确思维**：每个 `mcp_cua_driver_*` 失败先当"MCP 通道问题"，跑一次 `permissions status --json` 区分 daemon 层和 MCP 层
- **预防**：在 SKILL.md 加一条 pitfall："MCP not connected 不代表 daemon 死，先 `permissions status --json` 验 daemon 层"

## 沉淀进 SKILL.md 的内容

见 SKILL.md "cua-driver Daemon 与 MCP 生命周期" section，新增 4 条铁律 + 恢复序列 + 症状速查表。
