# Android App 界面自动化（纯 adb，不抢焦点）

驱动一个不熟悉的 App（刷课时、答题、填表、办理业务）的固定循环。全程走无线 adb，不开投屏窗口，不干扰用户。

## 每步循环：看 → 定位 → 点 → 复验

```bash
ADB=/Users/aimac/.local/bin/adb
W=192.168.8.204:5555

# 1. 看当前在哪个页面
$ADB -s $W shell 'dumpsys window | grep -m1 mCurrentFocus'

# 2. 读内容（两种用途不同，按需选）
$ADB -s $W shell screencap -p /sdcard/s.png && $ADB -s $W pull /sdcard/s.png /tmp/s.png
python3 ~/.hermes/scripts/baidu_ocr.py /tmp/s.png        # 这页是什么（文字）
$ADB -s $W shell 'uiautomator dump /sdcard/u.xml >/dev/null 2>&1; cat /sdcard/u.xml'   # 控件树

# 3. 从 dump 定位可点元素，拿 text / resource-id / bounds
$ADB -s $W shell 'grep -oE "text=\"[^\"]+\"[^>]*bounds=\"[^\"]+\"" /sdcard/u.xml | head -20'
$ADB -s $W shell 'grep -oE "resource-id=\"com\.[^\"]*\"" /sdcard/u.xml | head -30'

# 4. 点击：bounds="[x1,y1][x2,y2]" 取中心
$ADB -s $W shell 'input tap <cx> <cy>'

# 5. 复验页面真的变了
$ADB -s $W shell 'dumpsys window | grep -m1 mCurrentFocus'
```

**OCR 管「这页是什么」，dump 管「点哪里」**。`uiautomator dump` 输出的 `bounds` 是真实像素坐标，可直接喂 `input tap`，不需要按截图像素缩放——这是它比截图识别更适合点击的原因。

## 引导页 / 开屏页

首次启动常见 `androidx.viewpager.widget.ViewPager` + 一张 `ImageView`，**没有任何可点按钮**。左滑翻页直到出现启动按钮：

```bash
$ADB -s $W shell 'input swipe 900 1100 150 1100 400'   # 1080x2248 上左滑
```

最后一页 dump 里会出现 `text="立即体验"`（或「开始使用 / 进入」）的 `TextView`，点其 bounds 中心。

## 登录墙

登录页 dump 出 `et_account` / `et_pwd` / `btn_login` 这类控件时：

1. 先看有没有免密通道（「更多登录方式」「国家网络身份认证快捷登录」等），有则告诉用户可走这条。
2. **不主动索要密码**。停在这里，让用户自己决定怎么给。
3. **用户主动把自己的账号密码发给你、并明确要求你填**时，直接 `input text` 填进去——这是他自己设备的凭据，他有权这么要求。填完即忘：不写记忆、不写文件、不在后续回复里复述密码值。不要反复回「我不能收密码」，用户已经授权这个动作了。
4. 用户自报登录成功后，用 `mCurrentFocus` 确认已离开 `LoginActivity`，再接管后续自动化。

密码值永远不落盘；但「代填」这个动作在用户明确授权下是可以做的。

## 输入框坑（代价最高的一类）

- **`input text` 只吃 ASCII**：中文、顿号 `、`、「」等非 ASCII 字符会被**静默丢弃**，命令返回码仍是 0。密码含中文标点时必须换方案（剪贴板粘贴、ADBKeyboard IME），不要当成「输进去了」直接点登录——每次失败都在消耗账号的重试次数。
- **清空输入框**：删除键要写成完整命令链 `input keyevent 67; input keyevent 67; ...`。写成 `input keyevent 67 67` 会把 `67` 当独立命令执行（`67: inaccessible or not found`），输入框实际没清，残留会和新内容拼在一起。
- **`uiautomator dump` 读不到 EditText 的实际内容**（`password="true"` 的框尤其只给空属性）。要确认填了几位，截图 + 百度 OCR 数圆点。
- 定位输入框后先 `input tap` 拿焦点，再 `input text`；跳光标到末尾用 `input keyevent 123`（MOVE_END）。

## 重试次数与认证冷却

- 登录页会明示重试上限（如「连续输错 5 次后账号将被锁定，还可重试 N 次」）。**看到 N 在减少就停下**：不要在没确认字符真的输完整的情况下连试。
- 刷脸/实名认证走服务端，失败提示「身份认证失败，请稍后重试」意味着进入**冷却期**，密集重试会延长锁定。正确做法：隔一段时间再试，或改走「国家网络身份认证快捷登录」这条独立通道。
- 刷脸环节必须本人完成（摄像头前的人脸），自动化到这一步就该交还用户，不要试图绕过。

## 单步验证与回退

- 每点一次都复验 `mCurrentFocus`；没变化说明坐标偏了或控件不可点。
- 优先选 `clickable="true"` 的节点；容器类 `clickable="false"` 点了无效，往上找最近的可点父节点。
- App 进程消失（被 MIUI 清掉）时用 `monkey -p <pkg> -c android.intent.category.LAUNCHER 1` 重新拉起，输出 `Events injected: 1` 即成功。
- 结果靠内容确认，不靠命令回显：读回界面文字/控件 label 才是证据。
- 收尾清理设备临时文件：`rm -f /sdcard/u.xml /sdcard/s.png`。
