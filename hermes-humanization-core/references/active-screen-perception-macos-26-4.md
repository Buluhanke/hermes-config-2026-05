# 主动屏幕感知：macOS 26.4 失效与 CUA 替代方案

> 验证日期：2026-05-25
> 系统：macOS 26.4.1，Mac mini M4

## 核心问题

Hermes 无法主动看屏幕——只能被动等用户触发。peekaboo daemon 曾负责持续屏幕监控，但在 macOS 26.4 上彻底失效。

## peekaboo 失效根因

```
SCStreamError -3801 ("Could not start streaming")
```

- macOS 26.4 的 ScreenCaptureKit SCStream API 收紧，peekaboo 依赖的流式截图机制无法获取窗口
- `screencapture` 命令本身正常（CGWindowListCreateImage 路径），问题出在 peekaboo 的 SCStream 实现
- 权限全部已授权（TCC Screen Recording ✅），但 API 层面直接拒绝

## 当前可用的截图方案

| 方案 | 状态 | 备注 |
|------|------|------|
| `screencapture` 命令 | ✅ 正常 | CGWindowListCreateImage，命令行工具 |
| CUA `mcp_cua_screenshot` | ✅ 正常 | ScreenCaptureKit 兜底 CGWindowList，仍可用 |
| peekaboo SCStream | ❌ 失效 | macOS 26.4 彻底无法调用 |
| macOS 内置截屏 | ✅ 正常 | Shift+Cmd+6 等 |

**CUA screenshot 使用方式**（无需权限弹窗，已授权）：
```python
from hermes_tools import computer_use  # 导入 cua-driver MCP 工具
# 通过 mcp_cua_screenshot(window_id) 截图指定窗口
```

## 主动感知的缺口

即使 CUA screenshot 可用，当前架构问题是：**gateway 没有 hook 在消息入口处自动截图扫描**。用户触发 Hermes 时 Hermes 才行动，不会自己盯着屏幕发现弹窗。

要实现"主动感知"，需要在 gateway 消息处理链路前插入一个轻量级的屏幕状态检查 loop：
1. 新消息进来时
2. 先调用 CUA screenshot 抓前屏
3. 用 VLM 快速判断是否有弹窗/异常
4. 有异常则优先处理，无异常才走正常消息流程

## human_delay 配置

`~/.hermes/config.yaml` 第 335 行控制动作拟真开关：
```yaml
human_delay:
  mode: 'on'   # 'off' = 关闭，'on' = 开启
```

修改后需重启 gateway：
```bash
lsof -i :8642 -t | xargs kill
nohup ~/.hermes/hermes-agent/.venv/bin/hermes gateway run > ~/.hermes/logs/gateway.log 2>&1 &
```

验证：
```bash
launchctl list | grep hermes
curl -s http://localhost:8642/health | head -c 200
```

## 待解决

- [ ] gateway 消息入口 hook：消息进来时先截图扫一眼的机制需要代码实现
- [ ] peekaboo 替代品：是否值得重新编译 peekaboo 或找 SCStream 替代库
- [ ] 多窗口场景：当前 CUA screenshot 需要 window_id，如何自动发现需要关注的窗口

## 相关文件

- `humanization_core.py` — 已在用 CUA screenshot（capture_screen 回退路径）
- `vision_agent.py` — vlm_click 等视觉函数
- `config.yaml` 第 335 行 — human_delay mode