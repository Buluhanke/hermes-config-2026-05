# MI8 lamda Magisk 模块崩溃 — 2026-08-14 实测

## 问题

MI8 安装 FIRERPA lamda v10.4 Magisk 模块后，系统大量 app 提示"屡次停止运行"，Magisk App 本身也一直崩（"start timeout" → killed）。

## 根因

lamda v10.4 的 Frida 注入（底层依赖）与 MI8 Android 10 + SELinux enforcing 环境不兼容：
- avc denied → Frida 被 SIGKILL
- magiskd 本身还在跑（因为它是 root 进程）
- 但所有 app 的 zygote fork 出来的子进程全被 Frida 炸飞
- Magisk App UI 的 Provider 也因 attach timeout 被杀

## 修复步骤

### 1. 删除 lamda 模块

```bash
# 确认设备 IP（之前配过可能有残留）
adb disconnect
adb connect 192.168.8.204  # 可能变，看 adb devices
adb shell "su -c 'rm -rf /data/adb/modules/lamda /data/adb/modules/lamda.bak'"
```

### 2. 禁用所有 zygisk 模块

```bash
adb shell "su -c 'mkdir -p /data/adb/modules/zygisk_lsposed/disable'"
adb shell "su -c 'mkdir -p /data/adb/modules/zygisk_shamiko/disable'"
# 注意：必须是目录，不是空文件
```

### 3. 重启

```bash
adb shell "su -c 'reboot'"
```

### 4. 验证

重启后检查日志中是否还有新的 `failed to attach`：

```bash
adb shell "su -c 'logcat -d' 2>/dev/null | grep -E 'failed to attach|start timeout|Killing' | tail -10"
```

- 17:14 的崩溃是重启前的，可以忽略
- 重启后（17:24+）无新崩溃 = 修复成功

### 5. 如果 Magisk App 还崩

清除 App 数据后重试：

```bash
adb shell "pm clear com.topjohnwu.magisk"
adb shell "su -c 'reboot'"
```

## 禁用模块验证命令

```bash
# 验证 disable/ 目录是否存在
adb shell "su -c 'ls /data/adb/modules/zygisk_lsposed/disable'"
adb shell "su -c 'ls /data/adb/modules/zygisk_shamiko/disable'"
# 有输出即禁用成功
```

## MI8 当前状态（2026-08-14 修复后）

| 项目 | 状态 |
|------|------|
| lamda 模块 | 已删除 |
| lamda.bak | 已清理 |
| zygisk_lsposed | 已禁用 |
| zygisk_shamiko | 已禁用 |
| Magisk v30.7 | App 可正常打开 |
| 其他 App | 不再崩溃 |
| IP | 192.168.8.204:5555 |

## 教训

- Magisk App 崩 ≠ Magisk 本身坏了。Magisk daemon（magiskd）是 root 进程，存活没问题
- zygisk 模块（lsposed/shamiko/lamda）注入 zygote，所有 fork 出来的 app 进程都会受影响
- `disable/` 目录是 Magisk 禁用模块的标准方式，重启后自动生效
