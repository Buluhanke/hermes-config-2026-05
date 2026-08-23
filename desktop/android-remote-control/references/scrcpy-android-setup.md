# scrcpy + Android 远程控制安装记录

## 环境

### M4 Mac mini（当前 Host）
- 主机名: `AimacdeMac-mini`，用户: `aimac`
- IP: 当前 Mac
- scrcpy: `~/.local/bin/scrcpy` (Apple Silicon 版本 `scrcpy-macos-aarch64-v3.3.4.tar.gz`)
- adb: `~/adb-tools/platform-tools/adb`
- 软链接已创建: `~/.local/bin/adb → ~/adb-tools/platform-tools/adb`
- 设备检测: ✅ 正常（设备号 d0b859af）

### Intel Mac Pro（远程 Host）
- IP: `192.168.8.123`（不是 192.168.8.156，有双网卡：192.168.8.123 + 192.168.0.16）
- 主机名: `Mac-Pro`，用户: `mac`
- scrcpy: `~/.local/bin/scrcpy` (Intel 版本 `scrcpy-macos-x86_64-v3.3.4.tar.gz`)
- adb: `~/.local/bin/adb`（由 platform-tools 提取）
- phone 脚本: `~/.local/bin/phone`
- SSH: M4 Mac mini 可通过 `ssh mac@192.168.8.123` 无密码连接

### Android 设备
- 设备: Xiaomi MI 8（Android 10）
- 分辨率: 1080×2248
- IP: 192.168.8.204
- USB 设备号（有线）: d0b859af

## Intel Mac 安装命令（一次性）

```bash
# 安装 scrcpy（Intel 版本）
ssh mac@192.168.8.123 "cd /tmp && \
  curl -L 'https://github.com/Genymobile/scrcpy/releases/download/v3.3.4/scrcpy-macos-x86_64-v3.3.4.tar.gz' -o scrcpy.tar.gz && \
  tar -xzf scrcpy.tar.gz && \
  cp scrcpy-macos-x86_64-v3.3.4/scrcpy ~/.local/bin/ && \
  cp scrcpy-macos-x86_64-v3.3.4/scrcpy-server ~/.local/bin/ && \
  chmod +x ~/.local/bin/scrcpy ~/.local/bin/scrcpy-server"

# 安装 adb
ssh mac@192.168.8.123 "cd /tmp && \
  curl -L 'https://dl.google.com/android/repository/platform-tools-latest-darwin.zip' -o platform-tools.zip && \
  unzip -o platform-tools.zip && \
  cp platform-tools/adb ~/.local/bin/ && \
  chmod +x ~/.local/bin/adb"

# 创建 phone 脚本
ssh mac@192.168.8.123 "cat > ~/.local/bin/phone << 'EOF'
#!/bin/zsh
export PATH=\"\$HOME/.local/bin:\$PATH\"
adb start-server 2>/dev/null
scrcpy -m 1024 -b 15M --max-fps=30 --always-on-top
EOF
chmod +x ~/.local/bin/phone"
```

## phone 脚本（M4 Mac mini）

```bash
#!/bin/zsh
export PATH="$HOME/adb-tools/platform-tools:$HOME/.local/bin:$PATH"
scrcpy -m 1024 -b 15M --max-fps=30 --always-on-top
```

## phone 脚本（Intel Mac Pro）

```bash
#!/bin/zsh
export PATH="$HOME/.local/bin:$PATH"
adb start-server 2>/dev/null
scrcpy -m 1024 -b 15M --max-fps=30 --always-on-top
```

## 常见问题

### scrcpy 找不到 adb
scrcpy 硬编码在 `~/.local/bin/adb` 找 adb，PATH 有没有都不行。
**修复（M4 Mac mini）：**
```bash
ln -sf ~/adb-tools/platform-tools/adb ~/.local/bin/adb
```

### Android 设备完全检测不到（adb devices 为空）
排查顺序：
1. **手机 USB 模式是「仅充电」** — 下拉通知栏 → 点击 USB 通知 → 改成「文件传输(MTP)」或「PTP」。「仅充电」不暴露 USB 数据接口，adb 根本看不见设备。
2. **USB 调试未开启** — 开发者选项 → USB 调试 → 开启
3. **Xiaomi 额外安全设置** — 开发者选项 → 「USB 调试（安全设置）」需要开启
4. **授权弹窗未点** — 首次连接会弹出「允许USB调试」，需点「允许」

### Android 10 无音频
Android 10 不支持音频转发（需要 Android 11+），控制不受影响。

### Hermes 终端无法运行 scrcpy
scrcpy 需要图形显示上下文，Hermes 内置终端没有。必须在 Mac 的 Terminal.app 中执行。

### Intel Mac 双网卡问题
Intel Mac 有两个 IP：192.168.8.123（当前局域网）和 192.168.0.16。scrcpy 连接手机用 192.168.8.123 这个网卡。

## Root 恢复流程（BL 已解锁，待执行）

**背景：** MI 8 曾 root 过，系统更新（V12.0.3.0.QEAMIXM）后 root 失效，`su` 不可用，但 BootLoader 已解锁。

**步骤：**
1. 手机装 Magisk Manager（应用商店搜索或 GitHub 下载 APK）
2. 打开 Magisk Manager，按提示修补 boot.img 或直接刷入
3. Root 后设置持久化无线端口：
   ```bash
   adb shell su -c "setprop persist.adb.tcp.port 5555"
   ```
4. 重启验证：`adb connect 192.168.8.204:5555` 应该直接可用，无需 USB

**持久化端口效果：** 有 root + `persist.adb.tcp.port` 设置后，手机每次重启自动监听 5555，无需手动 `adb tcpip 5555`。
