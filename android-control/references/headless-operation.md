# 熄屏 / 锁屏下的 adb 操作

设备通过无线 adb 连接时，屏幕亮灭与 adb 通道无关：熄屏后 shell 命令、`input` 注入、`monkey` 启动 App 全部照常工作。因此用户锁屏离开不中断自动化。凭据（锁屏 PIN）只在当次会话内存使用，不写入任何记忆或文件。

## 状态判定

```bash
ADB=/Users/aimac/.local/bin/adb
W=192.168.8.204:5555
$ADB -s $W shell 'dumpsys power | grep mWakefulness= | head -1'   # Awake / Asleep
$ADB -s $W shell 'dumpsys trust | grep -m1 "User \"机主\""'   # deviceLocked=1 表示真锁屏
$ADB -s $W shell 'dumpsys window | grep -m1 mCurrentFocus'          # 当前前台窗口
```

`mWakefulness=Asleep` 只是熄屏，adb 照样操作；`deviceLocked=1` 才是需要解锁的锁屏态。机主以外用户（security space / XSpace）的 `deviceLocked=1` 是常态，只看机主那条。

## 熄屏下照常操作

`input keyevent`、`input tap/swipe/text`、`monkey` 启动 App 在 `Asleep` 下均生效，无需点亮屏幕。熄屏瞬间 adb 可能短暂显示 offline，重连即可：`adb connect <ip>` 返回 `already connected` 不影响后续命令。

## 点亮与解锁（MIUI）

1. **点亮**：`input keyevent 224`（KEYCODE_WAKEUP）比 `26`（电源键 toggle）可靠——26 在「刚熄屏又立刻点亮」时可能不生效，224 是明确的唤醒。
2. **确认锁屏界面**：点亮后 `uiautomator dump /sdcard/w.xml >/dev/null 2>&1; grep -oE 'resource-id="[^"]*"' /sdcard/w.xml`，出现 `com.android.systemui:id/keyguard_header` 即锁屏；出现 `com.miui.home` 则已直接进桌面，无需解锁。
3. **调出 PIN 盘**：从底部上滑 `input swipe 540 2000 540 800 400`（分辨率用 `wm size` 查，MI8 是 1080x2248）。dump 里出现 `com.android.systemui:id/keyguard_pin_view` 和「请用密码或指纹解锁」即成功。
4. **输 PIN**：`input text <PIN>` 对 PIN 盘有效（比逐键点击可靠）。
5. **验证解锁**：`dumpsys trust | grep -m1 "User \"机主\""` 看 `deviceLocked=0`。
6. 清理设备上的临时 dump 文件：`rm -f /sdcard/w.xml`。

`uiautomator dump` 在锁屏界面能读出控件文字（如「请用密码或指纹解锁」），比截图 OCR 更准且零成本；vision 模型余额不足时这是首选的界面识别手段。

## 重启后的额外一步：先解锁再碰存储

设备刚重启时 Pin 未输入，`/storage/emulated/0` 的任何写操作（`mkdir`/`cp`）会报 `Required key not available`，这是文件级加密（FBE）密钥未加载，不是权限或 root 问题。`/sdcard` 此时是指向 `/storage/self/primary → /mnt/user/0/primary` 的符号链，末端目录也可能还不存在——用 `/storage/emulated/0` real path 判断，别用符号链状态推断存储坏了。按上面步骤输 PIN 让 `deviceLocked=0`，再重试文件操作即可。

## 收尾

操作完把屏幕状态还原到用户离开时的样子（通常点亮 + 已解锁），并确认 `mWakefulness=Awake`、`deviceLocked=0`。
