# Android App 界面自动化（纯 adb，不抢焦点）

驱动一个不熟悉的 App（刷课时、答题、填表、办理业务）的固定循环。全程走无线 adb，不开投屏窗口，不干扰用户。

## 开始前必做：确认屏幕方向，坐标不跨会话复用

**每次点按前重新 dump 取 bounds，坐标不跨页面/跨方向复用。** `uiautomator dump` 的 `bounds` 是**当前方向**的真实像素，直接取中心即可；写死或缓存的坐标才会因页面加载、旋转、返回而失效。注意 `adb shell wm size` 只报物理尺寸、不随旋转变化，`screencap` PNG 与 dump bounds 才反映当前方向——别拿 wm size 推断当下横竖。
- 首页入口坐标会随页面内容漂移（例如多了「业务待办」卡片会把「学法减分」图标从 y≈876 推到 y≈1180）。**入口每次用 OCR 现定位**，不要记死某个 y；有「业务待办/参加学习教育」这类明确入口时优先走它。

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

**OCR 管「这页是什么」，dump 管「点哪里」**——这条只对原生控件页成立；H5/WebView 页 dump 拿不到任何文字和 bounds，坐标必须用切片 OCR 自己算（见下节）。`uiautomator dump` 输出的 `bounds` 是真实像素坐标，可直接喂 `input tap`，不需要按截图像素缩放——这是它比截图识别更适合点击的原因。

## H5 / WebView 页面（dump 只有 WebView 节点时）

政务、银行、交管类 App 的业务页常是内嵌 H5：前台 Activity 是 `*WebViewActivity`，`uiautomator dump` 只吐一个 `NAF="true"` 的 `android.webkit.WebView` 节点，没有任何子控件文字/bounds。此时别再 grep dump，改用截图 + 百度 OCR 切片自己算坐标。uiautomator2 的 `d(textContains=...)` 这类文本选择器打在 WebView 上会抛 `StackOverflowError`（递归遍历 Hybrid 树），同样别用——H5 页只有切片 OCR 这条路。

判据与截图：

```bash
$ADB $D shell "uiautomator dump /sdcard/u.xml >/dev/null 2>&1; grep -o 'NAF=\"true\"[^>]*WebView' /sdcard/u.xml"
$ADB $D shell screencap -p /sdcard/s.png && $ADB $D pull /sdcard/s.png /path/s.png
$ADB $D shell wm size    # 分辨率从这里取，别猜
```

坐标定位（先纵向切条定 y，再横向切块定 x）：

```python
from PIL import Image
import sys, os, time
sys.path.insert(0, os.path.expanduser('~/.hermes/scripts'))
from baidu_ocr import ocr
img = Image.open('/path/s.png')

def txt(box):
    img.crop(box).save('/path/_crop.png')
    return ' '.join(x['words'] for x in ocr('/path/_crop.png').get('words_result', []))

for y in range(0, 2560, 80):          # 纵向 80px 条带
    if '提交申请' in txt((0, y, 1600, min(y+80, 2560))):
        break
    time.sleep(0.3)
for x in range(0, 1600, 200):         # 横向 200px 块
    if '提交申请' in txt((x, y, min(x+200, 1600), y+80)):
        break
    time.sleep(0.3)
# 点块中心：input tap (x+100) (y+40)
```

- 百度 OCR 的 basic 接口只返回文字、不返回坐标，别指望它直接给 bounds；切片法就是坐标来源。
- 切条宽度取 80–120px：太宽把相邻行混进来，太窄文字被截断识别不出。
- 切片 OCR 逐次调用间隔 ~0.3s，避免限流返回空结果。
- 同页多个同名按钮（如两处「查看详情」）时记下所有命中的 y，按页面自上而下的步骤顺序判断点哪个；底部固定操作按钮通常在 y≈2400。
- 系统权限弹窗（如首次访问位置）是原生 `permissioncontroller` 控件，dump 正常可用，别用切片法。

## 政务/交管类业务：提交 ≠ 可继续

- 这类业务（学法减分、补贴申领等）提交后常有服务端审核闸门，页面会写明「等待审核 / N 个工作日内告知」。审核没过就没有可点的下一步，别反复点入口，也别编造进度。
- 汇报时给出申请号、提交时间、页面原文状态和解锁条件；把「已提交」和「已办完」严格区分。
- 需要本人刷脸/实名认证才能继续的环节交还用户，不要试图绕过。
- 已知包名：交管12123 = `com.tmri.app.main`；学法减分业务页是内嵌 H5（前台 `*WebViewActivity`），按切片 OCR 法操作。

## 长时挂机学习（刷课时 / 累计时长）

- 计时前先锁屏幕常亮并记原值，结束后还原：`OLD=$(adb -s $D shell settings get system screen_off_timeout | tr -d '\r')` → `adb -s $D shell settings put system screen_off_timeout 2147483647` → 收尾 `settings put system screen_off_timeout "$OLD"`。
- 挂机不是「点完就等」：每 ~20s 一轮 `screencap → pull → baidu_ocr.py`，按 OCR 文本分支处理，否则会错过弹窗：
  - 「本次学习结束 / 学习时长X」→ 点弹窗「确定」→ 回选课页继续下一条；
  - 「人脸 / 抓拍 / 认证 / 比对 / 拍照」→ **立刻停循环并通知用户本人处理**，不代刷——学习页会写明「人脸比对未通过本次学习无效」；
  - 「需学习…已学习…」→ 记累计进度，判断是否够时长。
- 抓拍时机不定：**可能一进播放页就弹，也可能播几分钟后才弹**。从点开视频那一刻起就轮询覆盖整个视频时长，别因为刚开播没弹就判「本条无抓拍」，也别以为进播放页就等于安全。
- 用户刷脸通过后**立刻自己恢复轮询继续往下学**，不要再等用户发「继续」——用户默认你会在识别通过后自动接管剩余流程，停着等指令会被当成卡住。
- 人脸抓拍弹窗（成功/失败页）是**原生控件**，dump 正常可用（`com.tmri.app.main:id/dialog_ok_btn` / 「再试一次」），别对它用切片 OCR。
- **采集完成 ≠ 比对通过**：`SilentLivenessActivity` 退出只代表摄像头采集结束，必须再读一次页面文字——若出现「人脸比对不通过，剩余 N 次」说明后端比对失败且有次数上限，再失败会作废本次学习/考试。
- **不替用户抢点「再试一次」**：用户不在摄像头前时点击就是消耗一次比对机会。停手→报进度和剩余次数→喊用户就位→等用户回话确认→再点。用户没回应就一直停着。
- 「已达到当前课件最大学习时长，请重新打开课件学习」→ 该视频已计满，**重复播放不再累计**。换未学过的卡片；零头用短视频补。
- **自动播下一条前必须等到终态**（「本次学习结束」或「已学习X分钟」数字增长），不能用固定短 sleep 连点卡片：以 6 秒间隔连点多个卡片，视频根本没真正播放，时长一分不涨还把卡片列表点光。循环用 `case` 匹配终态再推进，没到终态就继续 sleep 轮询。
- 视频卡片列表：**时长文字的 x 坐标不等于可点区域**，点时长标签常选中隔壁卡片。点下去后立刻 OCR 播放页标题+时长核对，不对就返回点相邻卡片的封面/标题区。
- 判定页面用 `dumpsys activity activities | grep mResumedActivity` 看 `XfjfStudySelectDocActivity`（选课）/ `XfjfStudyVideoLearningActivity`（播放）/ `SilentLivenessActivity`（抓拍）/ `XfjfExamOverviewActivity`（考完跳转），比每轮 OCR 便宜。
- 政务 H5 状态有缓存：审核通过后旧页仍显示「等待审核」。**返回上一级再进一次**刷新，别在缓存页上判定「还没通过」。
- 长时挂机（几十分钟）别在 `execute_code` 里跑超过 5 分钟的轮询循环——会触发 5 分钟超时、内核状态丢失。用 `terminal(background=true)` 起一个 bash 脚本，把分支结果追加写日志文件，主会话用 `sleep N; cat 日志` 分段查；脚本里 `dumpsys activity` + `uiautomator dump` 判状态，遇抓拍写标记并 `exit`，主会话读标记后喊用户。这样进度可恢复、也不占主会话超时预算。

## 原生考试页答题（学法减分考试等）

考试页是原生 Activity，dump 直接可读，别逐题走截图 OCR：

- 题干在 `text="N、..."`（`tv_sttg`），题型在 `tv_sttx`（单选题 / 多选题 / 判断题），题号格 `tv_index`，下一题 `btn_next`。
- 选项文本是 `text="A：..."` / `B：` / `C：` / `D：`，虽 `clickable="false"`，点 bounds 中心有效。判断题选项是 `text="Y：正确"` / `text="N：错误"`——按「正确/错误」grep 会漏，要匹配 `Y：`/`N：`。
- 判断题「Y：正确 / N：错误」的上下顺序**每题会变**（同一场里既出现 Y 在上 N 在下，也出现 N 在上 Y 在下），每次都从当前 dump 的 bounds 现算坐标，绝不记「正确在上方」这种固定位置。
- 用 Python 正则取选项坐标比 grep 稳：`re.findall(r'text="([ABCD][：:][^"]+)"[^>]*bounds="(\[[^\]]+\]\[[^\]]+\])"', xml)`，bounds 四数取中心即 `input tap` 坐标；判断题把 `[ABCD]` 换成 `[YN]`。
- **别靠 dump 里的 `selected="true"` 判断选项是否点上**：学法减分考试页选项读回来恒为 `selected="false"`（多选点完 A/B/C 后仍是 false），照它判断会以为全没选、白费时间。信 `bounds` 中心点击即可；真要核对就截图看选项前的勾选符号。翻页后重新读题号，别假设还停在同一题。
- 每题有倒计时（约 44–60s），别在单题上耗到超时；考试期间同样把 `screen_off_timeout` 设为最大，结束还原。
- **用户催速度时把整个答题循环压成一次工具调用**：一条 shell 里串完「点答案 → 点下一题 → dump 下一题」，Python 正则直接解析返回的 XML：
  ```bash
  adb shell "input tap X Y; sleep 0.35; input tap 800 2428; sleep 1.5; uiautomator dump /sdcard/e.xml >/dev/null 2>&1; cat /sdcard/e.xml"
  ```
  多选题在同一条 shell 里连续 tap 多个坐标（间隔 0.35s）再一次翻页。每题拆成「dump→判断→点击→翻页」多次工具调用的往返延迟会被用户当成卡住（原话「答题速度太慢，要快速点」）。判断答案仍由 agent 当场做，只是把 IO 合并。
- 结果页（考试不通过/通过）按钮**先 dump 找 bounds 再点**，别猜底部 y≈2440 盲点——结果页直接盲点会误触发「立即补考」，跳过错题回顾就开下一场。
- 交卷后错 3 题即不通过（90 分及格），补考次数与有效期有限：报告结果时给出剩余补考次数和时限，别急着自动再点。
- 考试内也会随机人脸抓拍：页面文字「系统将在3秒后进行人脸抓拍，请正对摄像头」是内嵌提示，真正识别弹窗是 `SilentLivenessActivity`。流程同挂机学习——停手、报进度、喊用户本人刷脸，通过后点「再试一次」重开识别。
- **看图题交还用户**：信号灯颜色、路口标线、事故情形这类题，OCR 只能读文字、读不出图中颜色/标线，不要蒙答案。默认分工报题号和题干原文，用户给答案后代点。文字题才由 agent 作答。

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
