---
name: macos-accessibility-tree-sniffer
description: macOS Accessibility Tree 全系统天眼 — 无截图、无OCR，直接穿透读取任意App的UI结构和物理坐标。触发：用户问"屏幕内容"、"读取桌面App"、"Mac系统级感知"。
tools: cua-driver, computer_use, pyobjc
---

# macOS Accessibility Tree 天眼

## 核心原理
macOS 为支持 VoiceOver（屏幕朗读器），强制在内存中为每个App维护完整的 **AXUIElement 树**：
- 每个按钮、输入框、菜单项 = AX节点
- 自带 Role / Title / Value / Position / Size
- 100% Unicode 纯文本，毫秒级读取，无需截图/OCR

## 两条通路

### 通路1：CuaDriver（已配置，推荐）
cua-driver 已在 Mac Mini 运行，走系统级 AX API，权限已授权。

**系统全览：**
```bash
echo '{}' | cua-driver call get_accessibility_tree
```
返回所有运行中的App + 可见窗口列表

**单App UI树（带 element_index 可直接 click）：**
```bash
# 先用 list_windows 找 window_id
cua-driver list_windows
# 然后抓具体窗口
echo '{"pid":21093,"window_id":33778}' | cua-driver call get_window_state
```
返回：Markdown格式的完整UI树，每个可交互元素带 `[element_index N]`，直接发给 `cua-driver call click` 即可点击。

**权限状态：**
```bash
cua-driver permissions status
```
已验证：Accessibility ✅ Screen Recording ✅

### 通路2：Python pyobjc（直接C调用，绕过cua-driver）
```python
from ApplicationServices import (
    AXUIElementCreateSystemWide,
    AXUIElementCopyAttributeValue,
    kAXFocusedApplicationAttribute,
    kAXRoleAttribute, kAXTitleAttribute, kAXValueAttribute,
    kAXPositionAttribute, kAXSizeAttribute, kAXChildrenAttribute,
)
# 读取前台App的AX树
system_wide = AXUIElementCreateSystemWide()
_, focused_app = AXUIElementCopyAttributeValue(system_wide, kAXFocusedApplicationAttribute, None)
```

注意：前台是 loginwindow（锁屏）时无法读取，需 Mac 处于正常桌面状态。

## 已验证成果（2026-06-02）

Chrome 打开 DeepSeek 页面的 AX 树输出：
- **1974 个节点**，完整菜单/书签/地址栏/页面内容全部可读
- 每个节点：`[element_index N] AXRole "title" [actions=...]`
- 书签栏里数千条历史记录全部可见（隐私注意）
- 纯文本输出，无需截图，无需OCR

## 对比传统方案

| 维度 | AX Tree | 截图OCR |
|------|---------|---------|
| 准确率 | 100% Unicode | 依赖模型 |
| 速度 | 毫秒级 | 秒级 |
| 遮挡 | 无视遮挡 | 必须可见 |
| 熄屏 | 内存可读* | 不可用 |
| 坐标 | 自带物理坐标 | 需二次计算 |

*需 Mac 未休眠，屏幕可关闭

## 点击操作
```bash
# 用 element_index 直接点击（无需坐标）
echo '{"pid":21093,"element_index":123,"window_id":33778}' | cua-driver call click

# 或用物理坐标点击
echo '{"pid":21093,"x":150,"y":300}' | cua-driver call click
```

## 注意事项
1. 书签/历史记录会被完整读出，使用前注意隐私
2. AXUIElementCopyAttributeValue 偶尔返回 error=-25204，原因是目标App不支持AX或前台是loginwindow
3. Chrome 书签菜单节点极多（1900+），需要 depth 限制或 query 过滤
4. cua-driver 版本 0.3.4，GitHub 有 0.5.1 可更新（`cua-driver update --apply`）

## CLI 一行命令速查
```bash
# 看当前系统所有窗口
cua-driver list_windows 2>/dev/null | python3 -c "import sys,json; [print(w['app_name'], w['title'], 'pid:', w['pid'], 'wid:', w['window_id'], 'on_screen:', w['is_on_screen']) for w in json.load(sys.stdin).get('windows',[]) if w.get('is_on_screen')]"

# 读备忘录的UI树
cua-driver list_windows 2>/dev/null | python3 -c "import sys,json; wins=[w for w in json.load(sys.stdin).get('windows',[]) if '备忘录' in w.get('app_name','')]; print(wins)"
```