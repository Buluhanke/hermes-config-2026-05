# MCP config.yaml 结构说明

## 三层 YAML keys 与 hermes-agent 的对应关系

| 行号 | Key | 层级 | 类型 | 状态 |
|---|---|---|---|---|
| 471 | `servers: {}` | `lsp.servers` | dict | ✅ 正常 |
| 494-496 | `mcp: servers: '{...}'` | `mcp` (顶层键) | **string（损坏）** | ⚠️ 字符串序列化 |
| 497-502 | `mcp_servers:` | 顶层键 | dict | ✅ 正常（H17格式） |
| 503 | `servers: ''` | 顶层键 | string | ⚠️ 残留垃圾 |

## 损坏原因

`hermes config set mcp.servers '{"cua-driver": {...}}'` 通过 `pyyaml.dump()` 存储时，
整个值被当作字符串序列化进了 `mcp:` 顶层键，而不是写入 `mcp_servers:` 块。

## 正确的添加 MCP server 方式

### 方式1：hermes mcp add（交互式，推荐）
```bash
hermes mcp add cua-driver --command /Users/aimac/.local/bin/cua-driver --args mcp
```
写入 PTY 自动确认：`hermes mcp add cua-driver --command /path --args mcp <<< "Y"`

### 方式2：Python yaml（编程式，精确控制）
```python
import yaml

path = '/Users/aimac/.hermes/config.yaml'
with open(path) as f:
    cfg = yaml.safe_load(f)

# 方式A：在 mcp_servers 块中添加/更新
cfg.setdefault('mcp_servers', {})
cfg['mcp_servers']['cua-driver'] = {
    'command': '/Users/aimac/.local/bin/cua-driver',
    'args': ['mcp'],
    'env': {}
}

# 方式B：替换整个 mcp.servers（顶层 mcp: 键）
cfg['mcp'] = {'servers': cfg['mcp_servers']}  # 同步到正确位置

with open(path, 'w') as f:
    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
```

## 不要用的方式

- `hermes config set mcp.servers '{...}'` — 存储为字符串
- `hermes config set fallback_providers "[{...}]"` — 存储为字符串

## MCP 服务器配置读取优先级

1. `mcp_servers`（顶层键，H17格式）← **实际读取位置**
2. `mcp.servers`（顶层 mcp: 的子键）← 备用/兼容

## 当前 cua-driver 配置

```yaml
mcp_servers:
  cua-driver:
    command: /Users/aimac/.local/bin/cua-driver
    args:
      - mcp
    enabled: true
```

可用工具：35个（list_apps, list_windows, get_window_state, launch_app, kill_app, bring_to_front, click, double_click, right_click, drag, type_text, press_key, hotkey, set_value, scroll, get_screen_size, get_cursor_position, move_cursor, set_agent_cursor_enabled, set_agent_cursor_motion, set_agent_cursor_style, get_agent_cursor_state, check_permissions, get_config, set_config, get_accessibility_tree, zoom, page, start_recording, stop_recording, get_recording_state, replay_trajectory, start_session, end_session, check_for_update）

## 清理残留字段的 Python 脚本

```python
import yaml

path = '/Users/aimac/.hermes/config.yaml'
with open(path) as f:
    lines = f.readlines()

# 删除 mcp: 顶层块内的损坏 servers 行（495-496行附近）
# 删除顶层的 servers: '' 空字符串行（503行附近）
# 不touch lsp.servers: {}（471行）

cleaned = []
skip_mcp_servers_string = False
for line in lines:
    # 跳过 mcp: 顶层块内的 string-serialized servers 行
    if "servers: '{" in line or 'servers: \'' in line:
        skip_mcp_servers_string = True
        continue
    if skip_mcp_servers_string and line.strip().startswith('mcp'):
        skip_mcp_servers_string = False
    # 跳过顶层空字符串 servers: ''
    if line.strip() == "servers: ''":
        continue
    cleaned.append(line)

with open(path, 'w') as f:
    f.writelines(cleaned)
```