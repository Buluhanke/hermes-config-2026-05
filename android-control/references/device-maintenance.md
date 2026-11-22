# Android 设备维护 — 存储清理与侧载 App

## 铁律：先分类再删

清理前把目标分成三类并列出清单，向用户确认范围后才动手：

1. **可再生缓存** — 可删：聊天软件自动下载的媒体（Telegram Video / Telegram Images、Thundergram `x_account*/photos|videos|temp`、微信 `MicroMsg` 外的 `cache/`）。删后 App 按需重新下载，不影响聊天记录和登录。
2. **账号与用户数据** — 永不删：`MicroMsg/`、Telegram `x_account*/` 账号目录、`shared_prefs/`、`databases/`、Documents；用户名下的照片、下载文件。用户明确要求「清理不能影响登录的账号」时，这类一律不动。
3. **系统关键文件** — 永不删：`/data/local/tmp/server`、`/data/local/tmp/usr`（FIRERPA lamda 运行时，删了远程控制全废）；`boot.img` / `stock_boot.img` / `new-boot.img` / `kernel_dtb` / `ramdisk.cpio` / `magisk*.apk`（刷机与 root 恢复备份，删了可能变砖）。

## 排查命令

```bash
ADB=/Users/aimac/.local/bin/adb   # Hermes 终端 PATH 里没有 adb，用全路径
W=192.168.8.204:5555

$ADB -s $W shell df -h /sdcard                       # 总使用率
$ADB -s $W shell 'du -sk /sdcard/* 2>/dev/null | sort -nr | head -30'
$ADB -s $W shell 'du -sk /sdcard/Android/data/* 2>/dev/null | sort -nr | head -20'
$ADB -s $W shell 'du -sk /data/local/tmp/* 2>/dev/null | sort -nr | head -20'
```

Android toybox 的 `sort` 没有 `-h`，用 `du -sk` + `sort -nr`（单位 KB）。

## 清理后的验证

- `df -h /sdcard` 对比清理前后可用空间
- 关键账号目录仍在：`MicroMsg`、`x_account*`、`Telegram Documents`
- 刷机备份与 lamda 运行时未动

## adb 授权失效的修复边界

`unauthorized` 时删 `~/.android/adbkey*` 能触发重新配对，但**无线连接下授权弹窗只能在设备屏幕上点**——Hermes 够不着手机屏幕。必须让 USB 连着并授权一次。`adb tcpip 5555` 重新开启无线调试前，先 `adb disconnect <ip>` 断开旧无线连接，避免同一台设备出现两个 selector 导致命令歧义；执行后等 3 秒再 `adb connect`，并用 `adb -s <ip> shell echo OK` 和 `getprop service.adb.tcp.port` 验证。

## 侧载 App（以官方包为准）

1. 先确认包名和官方开发者（如交管12123：`com.tmri.app.main`，公安部交通管理科学研究所）。
2. 从下载站页面 HTML 里 grep APK 直链：`curl -sL <page> | grep -oE 'https?://[^"<> ]+\.apk[^"<> ]*'`；优先选大厂应用商店 CDN（如 `imtt.dd.qq.com`）。不要直接装来路不明的镜像。
3. 下载后**校验 MD5 与发布页标注一致**再装：`md5 -q <file.apk>`（macOS）。
4. `adb -s <device> install -r <file.apk>`；成功用 `pm list packages | grep <pkg>` + `dumpsys package <pkg> | grep versionName` 验证版本。
5. 装完删除本地 APK，不给刚清理过的手机/本机留垃圾。

## 升级 App 而不丢配置

先查新版本**是否改了包名**（release notes 或下载页的"程序包名称"）。这一条直接决定方案：

| 情况 | 做法 | 配置 |
|---|---|---|
| 包名不变 | `adb install -r <apk>` | 直接保留，数据目录不变 |
| 包名变了 | `install` 不报错但两版并存，旧配置**不迁移** | 走 App 自带的导出→导入；root 直接搬数据目录只适合同 schema 的小版本 |

**包名 + 大版本同时变时，直接搬数据目录会崩**：旧库的 Room schema 与新版本不匹配，`androidx.work` 等系统表在启动时报 `FrameworkSQLiteOpenHelper.getWritableDatabase`，App 直接闪退。改包名后再 `adb restore` 也不行——备份 `_manifest` 里的签名证书是旧包的，恢复到新包名会因签名不匹配报「未安装应用」。这两条路都不要试，**先找 App 自带的跨版本导出/导入**（常见于「一键换新机 / 迁移助手」，入口可能在「主动控制·客户端」这类子功能里，不在通用设置）。

### 定位隐藏的迁移入口：扫 dex 类名

迁移功能往往是一个没有 launcher 入口的 Activity，在设置页里翻不到。不要靠滑菜单碰运气，直接从 APK 里把类名列出来：

```python
import zipfile, re
z = zipfile.ZipFile(apk_path)
for fn in z.namelist():
    if fn.endswith('.dex'):
        data = z.read(fn)
        for c in re.findall(rb'L<包名路径>/[A-Za-z0-9_/$]*(?:activity|ui|page|screen)[A-Za-z0-9_/$]*;', data):
            print(c.decode().replace('L','').replace(';','').replace('/','.'))
```

中文功能名（如「一键换新机」）也能在 dex 字符串池里搜到，但字符串池和类名是分开存的，**搜中文字符串拿不到类名**——必须单独扫 `L…;` 类签名。找到候选 Activity 后直接拉起，跳过所有 UI 寻找：

```bash
$ADB -s $W shell 'am start -n <pkg>/<pkg>.activity.ClientActivity'
$ADB -s $W shell 'dumpsys window | grep -m1 mCurrentFocus'   # 确认真的到了目标页
```

### 离线导出/导入的实测流程（跨包名 + 跨大版本可用）

以「一键换新机」为例，进页面后切到**离线模式**（默认是网络模式，需要服务端，用不了）：

1. **旧版导出**：离线模式 → 「导出」，产出 `/storage/emulated/0/Download/<App>.json`。文件里应能看到 `rule_list` / `sender_list` / `task_list` / `version_name` 等键——`version_name` 记录的是导出端版本。
2. **旧版导出的 JSON 先 pull 到 Mac 留底**，再让新版导入，避免新版导入覆盖后无法回滚。
3. **新版导入**：同一入口 → 离线模式 → 「导入」。

关键判断：UI 上会写「导出方与导入方的 APP 版本必须一致」，但**新版通常带版本兼容映射表，跨大版本导入能成功**——判断依据是新版 release notes 里有没有「兼容旧版本导入」这类条目，有就直接试，不要被这句提示劝退。

导入成功的标志是弹「导入配置成功！需要重启 APP 以便生效！」。之后必须做三步验证：重启 App（`am force-stop` + 拉起）→ 看「转发规则」「发送通道」页实际条目 → 点进通道详情确认令牌等敏感字段位数正确（令牌只会显示为圆点，数圆点个数对比原值长度）。

官方还提示两项导入后必须人工补的动作：发送通道/转发规则会被完全覆盖且清空历史，而「主动请求、保活措施、个性设置」**不在克隆范围**——导入后要再进一次通用设置把需要的开关各开一次。

包名变了时的备份手段，按可靠性排序：

1. **root 直接打包整个数据目录**（唯一完整的）：`su -c 'tar czf /sdcard/<pkg>.tgz /data/data/<pkg>'`，再 pull 出来。
2. **App 自带导出**（如"一键换新机"→离线导出）：产出专用格式，能跨包名导入，但入口在 UI 里不一定好找。
3. **`adb backup -apk <pkg>`**：不需要 root，但**有盲区，不能当完整备份**。

`adb backup` 的盲区：它按 App 的 backup rules 取文件，能拿到 `shared_prefs/`（全局设置、开关、SIM 备注等）和 `d_sp/`，但 SQLite 主库常**只备份到 `-shm` 而缺主库本体**——规则、通道、令牌这类存在 db 里的东西全拿不到。`am force-stop` 后再备份也不能解决。

验证备份是否真的完整：解开头 4 行（`ANDROID BACKUP` / version / compressed / `none`），余下是 zlib，用 python `zlib.decompress` + `tarfile` 列出条目，确认 `db/*.db` 主库在列——**只看文件大小会骗过自己**。

判断配置到底存在哪：`d_sp/<pkg>.xml` 里的键如果只有开关/设备名/SIM 之类的全局项，那规则和发送通道就必然在 db 里，必须走 root 方案。

## Root 设备上的 App 闪退：区分包损坏与反 root 检测

银行/政务类 App 在已 root 设备上常在加固库的 `JNI_OnLoad` 主动 abort。诊断顺序固定，不要凭「ClassNotFoundException」或 ABI 字样猜架构问题：

1. `adb logcat -c` → 启动 App → `logcat -d | grep -iE 'FATAL|Exception|signal|crash' | tail`。
2. 找 `beginning of crash` 后的 native `backtrace`，看具体哪个 `.so` 的哪个函数 abort。`java.lang.ClassNotFoundException: androidx.core.app.CoreComponentFactory` 是无害的 fallback 日志，**以 native backtrace 为准**。
3. backtrace 指向加固/安全库（如 `libashield.so`）的 `JNI_OnLoad` + `SIGABRT` → 判定为反 root 检测，不是包损坏、不是 32/64 位问题。交叉验证：所有官方渠道的包 MD5 相同时，不存在「换 arm64 版」这条路。
4. 确认 root：`adb shell 'id; ls /sbin/su'` + `pm list packages | grep -i magisk`。

修复 = Magisk Zygisk DenyList 隐藏 root（前提 `zygisk=1`）：

```bash
# 1. 拉 db 到 Mac（手机无 sqlite3 CLI）
$ADB -s $W shell 'su -c "cp /data/adb/magisk.db /sdcard/m.db"' && $ADB -s $W pull /sdcard/m.db ~/magisk.db
# 2. Mac 上 python3 sqlite3 改：denylist 表 DDL 为 (package_name TEXT, process TEXT)
#    INSERT OR IGNORE INTO denylist VALUES ('<pkg>', '')   # process 空 = 全进程
# 3. 推回并恢复权限
$ADB -s $W push ~/magisk.db /sdcard/m2.db
$ADB -s $W shell 'su -c "cp /sdcard/m2.db /data/adb/magisk.db; chmod 600 /data/adb/magisk.db; chown root:root /data/adb/magisk.db"'
# 4. 回读验证 denylist 记录真的落盘，再 force-stop + 重开 App
$ADB -s $W shell 'am force-stop <pkg>; monkey -p <pkg> -c android.intent.category.LAUNCHER 1'
$ADB -s $W shell 'dumpsys window | grep -m1 mCurrentFocus; ps -A | grep <pkg>'
```

最后用百度 OCR 读截图确认是正常首页而非报错页。若重启后 App 又闪退，重新检查 denylist 记录是否还在。
