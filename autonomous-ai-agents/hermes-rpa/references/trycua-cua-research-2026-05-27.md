# trycua/cua 调研 — 2026-05-27

## 基本信息

- **GitHub**: https://github.com/trycua/cua
- **Stars**: 17.1k（2026-05-27）
- **定位**: 开源计算机控制Agent基础设施（Sandbox + SDK + Benchmark）

## 核心组件

### 1. Cua Driver（macOS后台控制）

**安装**：
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"
```

- Swift编写，走MCP over stdio协议
- 后台运行，不抢占焦点（focus/space）
- 支持非AX表面（Chromium web content、Canvas类工具：Blender/Figma/DAW）
- 每session自动录制为可回放trajectory

**关键功能**：
- `cua do switch host` — 连接本机（需一次 `cua do-host-consent` 授权）
- `cua do screenshot` — 截图
- `cua do click x y` — 点击
- `cua do snapshot "指令"` — AI标注屏幕+返回元素坐标（需ANTHROPIC_API_KEY）
- `cua trajectory share` — 上传回放获取分享链接

### 2. Window Zoom（精确点击核心技巧）

**痛点**：点击小按钮、密集UI元素时坐标漂移。

**解法**：
```bash
cua do zoom "Google Chrome"   # 裁剪到目标窗口，坐标变成窗口相对
cua do screenshot              # 放大视图
cua do click 112 44             # 精确点击小元素
cua do unzoom                   # 恢复全屏坐标
```

**原理**：放大到窗口后截图，分辨率不变但显示区域缩小，等效坐标精度翻倍。

**适用场景**：
- 小按钮（< 30px）
- 密集表单元素
- 坐标不确定时

### 3. Look → Act → Verify 循环

每次UI变化后立即重新截图验证。坐标会过期，必须重新感知。

### 4. Trajectory 回放

所有操作自动录制到 `~/.cua/trajectories/{machine}/{session}/`，
可 `cua trajectory share` 生成可分享链接。

## 与 Hermes 的关系

**可借鉴点**：
1. Window Zoom思路 → hermes-rpa skill 中"精确点击小元素"流程
2. Trajectory回放 → 调试/复盘
3. AI snapshot（需API Key）→ 未来可做本地VLM替代

**不直接替换**：
- Hermes已有 `computer_use` (cua-driver) 实现类似功能
- 安装cua-driver可扩展MCP工具生态（多一个独立通道）

## 安装状态

- ✅ `pip install cua` 成功（cua Python包）
- ⚠️ cua-driver Swift binary 需 root/授权

## 参考

- https://github.com/trycua/cua
- https://cua.ai