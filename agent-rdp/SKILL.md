---
name: agent-rdp
description: AI远程控制Windows电脑的技能。通过RDP协议连接目标Windows机器，截图、鼠标、键盘、剪贴板、UI自动化、OCR文字识别。触发：远程控制/控制Windows电脑/远程协助/处理电脑故障/ RDP连接
---

# agent-rdp — AI远程控制Windows电脑

基于 IronRDP 的 CLI 工具，无需在目标Windows安装任何软件，直接用Windows自带远程桌面服务。

## 前提条件

**目标Windows电脑：**
- 开启远程桌面（系统属性 → 远程 → 允许远程连接）
- 需要有网络连接（同一局域网或可通过IP访问）
- 需要有登录账号密码

## 连接命令

```bash
# 最安全：密码通过 stdin 输入（避免密码出现在进程列表）
echo '密码' | agent-rdp connect --host <目标IP> --username <用户名> --password-stdin

# 或环境变量
export AGENT_RDP_USERNAME=Administrator
export AGENT_RDP_PASSWORD=secret
agent-rdp connect --host <目标IP>
```

## 核心操作

```bash
# 截图（存文件或base64）
agent-rdp screenshot --output desktop.png
agent-rdp screenshot --base64

# 鼠标操作
agent-rdp mouse click <x> <y>
agent-rdp mouse right-click <x> <y>
agent-rdp mouse double-click <x> <y>
agent-rdp mouse move <x> <y>
agent-rdp mouse drag <x1> <y1> <x2> <y2>

# 键盘输入
agent-rdp keyboard type "Hello 你好"
agent-rdp keyboard press Ctrl+C
agent-rdp keyboard press Alt+Tab

# OCR定位文字（找屏幕上文字的坐标）
agent-rdp locate "确定"
# 返回 {x, y} 可用于 mouse click

# Windows UI自动化（无障碍API，更精准）
agent-rdp automate snapshot     # 获取UI元素树
agent-rdp automate click "@e5" # 按元素引用点击
agent-rdp automate fill "@e7" "内容"

# 剪贴板
agent-rdp clipboard read
agent-rdp clipboard write "要复制的文本"

# 查看远程桌面（网页浏览器）
agent-rdp view
```

## 工作流

1. `connect` 建立RDP会话
2. `screenshot` 或 `automate snapshot` 查看远程桌面状态
3. `mouse`/`keyboard`/`automate` 执行操作
4. `disconnect` 结束会话

## OCR文字定位示例

```bash
# 找"确定"按钮的位置
RESULT=$(agent-rdp --json locate "确定")
# 返回: {"text":"确定","bounds":{"x":850,"y":550,"width":80,"height":30}}
# 然后点击
agent-rdp mouse click 890 565
```

## 坑点

- 密码包含特殊字符时用单引号括起来
- 目标Windows需要同一网络或可通过IP访问
- 首次连接可能需要在Windows上确认证书

## 跨平台备选（见 references/remote-access-landscape.md）

- **macOS/Linux** → `pip install vnc-computer-use` + 目标开VNC
- **无头Linux** → computer-use skill（Xvfb虚拟桌面）
- **多系统混合** → GhostDesk（Docker）
