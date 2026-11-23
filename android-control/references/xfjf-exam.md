# 交管12123 学法减分 全流程自动化（纯 adb）

从申请到减分完成的完整路径。全程无线/USB adb，不开投屏窗口。

## 阶段

1. **申请**：首页「学法减分」→ 在线申请 → 弹位置权限选「仅使用期间允许」→ 选「网上学习」→ 提交。H5 页面 `uiautomator dump` 读不到文字，用截图+百度OCR按条带扫描定位按钮（把整图切成 y 条带逐个 OCR，找到关键词后再切 x 条带细化）。
2. **审核**：提交后状态「已提交，等待审核」，官方一个工作日内短信通知。审核通过后重进页面点「去学习」——**第一次点可能报「未查询到驾驶证信息」，返回再点一次就好**（接口瞬时故障）。
3. **学习**：30 分钟，看视频累计。学习页底部「开始学习」→ 选视频 → 播完弹「本次学习结束」点确定 → 回选课页。**每个视频有最大学习时长，重复播同一个不再计时**，必须换下一个。选课页每个视频带状态标记（「未开始」/「已学完」）——**只点「未开始」的**；已学完的再点会弹「已达到最大学习时长」且不计时。**必须等当前视频真正播完（弹「本次学习结束」）再点下一个**：后台轮询脚本几秒就切一个卡片会让学时进度卡住（切走的视频没播完不计时长），实测进度停在 82% 就是这个原因。视频卡片坐标每次从当前 dump 的 bounds 现取（时长文字的 x 不等于可点区，点卡片封面/标题），零头用短视频补。选课页状态文字用 `adb shell uiautomator dump` 读得到，同一页 uiautomator2 的 `dump_hierarchy()` 可能返回空——读状态优先用 adb dump。
4. **考试**：20 题，44 秒/题，90 分及格（最多错 2 题），有 2 次补考。点「开始考试」→ 倒计时 → 逐题作答 → 交卷。
5. **最终认证**：交卷后「请把脸移入圈内保持不动」，5 分钟限时。通过后显示「考试通过...答对20道题...已为您提交减分申请」。

## 补考（考试不通过后）

交卷后若显示「考试不通过 / 本次考试不合格，答错N题或考试未完成，剩余补考次数N次，请在24小时内完成补考」，当前页面是 `ResultActivity`，含「错题回顾」和「立即补考」按钮。先读结果页文字确认剩余次数与时限，再按当次 dump 的 bounds 取「立即补考」中心点击即重开 20 题（题目全新，非原题）。补考流程与首考完全一致：人脸抓拍本人完成 → u2 逐题快答 → 交卷 → 最终认证。点完「立即补考」用 `xfjf_wait.py reexam-ready` 监听题目页出现，别空等；交卷后用 `xfjf_wait.py final-auth` 监听最终认证结果。

## 学时达标的终态弹窗（易漏）

凑够 30 分钟时弹的不是「本次学习结束」，而是「累积学时已满30分钟，请尽快提交完成学习」+「提交」按钮（竖屏 1600x2560 下按钮中心约 (1600,896)，仍以当次 dump bounds 为准）。自动学习循环若只识别「本次学习结束」/「人脸」/「最大学习时长」，会漏掉这个终态一直空转——状态机必须把「累积学时已满」/「提交」也算作退出条件，人工补点即可。

收尾链：点「提交」→「提交成功」→「确定」（竖屏约 (1280,869)）→ 跳 `XfjfExamOverviewActivity`（学法减分考试总览页：20 题 / 2 次补考 / 7 天有效期）。此时学习阶段彻底完成，考试停在这一页等人到位再点「开始考试」。收尾把 `screen_off_timeout` 恢复原值、清理临时 xml。

## 提速：uiautomator2 常驻（强烈推荐）

裸 `adb shell uiautomator dump` 每次冷启动 JVM + 等 1 秒 idle，**实测 2.8 秒/次**——这是逐题答题慢的根因。uiautomator2 常驻设备端服务，实测 dump **0.2 秒**（13x）、click 0.23 秒。脚本 `scripts/xfjf_fast.py` 已封装：

```bash
U=~/.hermes/venvs/u2/bin/python
$U scripts/xfjf_fast.py read          # 读当前题(JSON)
$U scripts/xfjf_fast.py ans A         # 答一题并翻页，返回下一题
$U scripts/xfjf_fast.py batch 'A,N,Y,ABC,...'  # 批量，一次跑完不等模型
```

首次 `u2.connect()` 会自动 push jar 拉起服务。venv 已建在 `~/.hermes/venvs/u2`（清华源装 uiautomator2）。

**事件驱动等待**（配合 `terminal(background=True, notify=True)`，完成瞬间收到通知，不空等）：
```bash
U=~/.hermes/venvs/u2/bin/python
$U scripts/xfjf_wait.py unlock-start  --dev <IP>:5555  # deviceLocked=0 瞬间点亮+点「开始考试」+报首题
$U scripts/xfjf_wait.py face-pass     --dev <IP>:5555  # 抓拍通过、题目页出现即报题目JSON
$U scripts/xfjf_wait.py reexam-ready  --dev <IP>:5555  # 点「立即补考」后题目页出现即报；抓拍态单独报
$U scripts/xfjf_wait.py final-auth    --dev <IP>:5555  # 交卷后最终认证通过/失败/超时即报
```

**更快的方向**：题库 API（如 shujuyu.cn `/v1/api/xuefa/query`，¥0.002/次）可在脚本内直接匹配题干拿答案，把「模型逐题判断」也从热路径拿掉——20 题批量跑完约 20 秒，无需每题一次 LLM 往返。看图题题库带 `images` URL，可配合图色分析。**该 API 需付费 key（URL 参数 `key` 或 Header `Authorization`），无 key 直接 HTTP 401 `缺少API认证参数`**——开考前先确认有 key，没有就走下面的像素秒判法，别把时间押在未验证的 API 上。注意：任何自动答题都绕不过随机人脸抓拍，那一秒必须本人。

## 刷题循环（原生页，dump 可读）

考试页是 `ExamActivity`，`uiautomator dump` 能拿到题干/选项/坐标，比 OCR 快且准：

```bash
ADB=/Users/aimac/.local/bin/adb
D="-s <设备>"
# 一条命令完成：点答案 → 下一题 → dump 下一题
$ADB $D shell "input tap <答案x> <答案y>; sleep 0.6; input tap 800 2428; sleep 1.5; uiautomator dump /sdcard/e.xml >/dev/null 2>&1; cat /sdcard/e.xml"
```

Python 解析（execute_code 里每次调用跑一题，答案由模型判断后填入坐标）：

```python
q=re.search(r'text="(\d+、[^"]+)"',xml)
typ=re.findall(r'text="\(([^)]+)\)"',xml)[:1]
for t,b in re.findall(r'text="([ABCDYN][：:][^"]+)"[^>]*bounds="(\[[^\]]+\]\[[^\]]+\])"',xml):
    n=re.findall(r'\d+',b); cx,cy=(int(n[0])+int(n[2]))//2,(int(n[1])+int(n[3]))//2
```

**铁律：Y/N 位置每题会变**（有时 Y 在上 731、有时 N 在上 731），必须每次从 dump 实时读 text 和 bounds，绝不能记死坐标。多选题也是点选项 + 点下一题，没有独立提交按钮；最后一题底部按钮文字变成「交卷」，坐标仍是 (800,2428)。`selected` 属性读不出来（app 用自定义绘制），靠截图 OCR 看方框符号确认。

学习和考试**都会**强制人脸抓拍——视频一播放就弹，不刷脸进不了播放页，不存在"用户不在先挂机学课时"的可能。抓拍失败有次数上限（提示"剩余 N 次"），耗尽会让本次学习/考试作废。用户不在时**绝不要反复点"再试一次"**，停在识别页等用户到位再触发。

**锁屏态 ≠ 考试抓拍（u2 face 假阳性）**：华为平板锁屏页自带"双击屏幕进行人脸识别"和知识问答卡片（如"中国鹿类有哪些？"），`xfjf_fast.py` 的 `parse()` 用 `'人脸' in xml` 判 face，锁屏时会给出 **face:true 假阳性**。判据三件套：① `adb -s <dev> shell dumpsys trust | grep -m1 deviceLocked` → `deviceLocked=1` 就是锁屏，先解锁；② `dumpsys activity activities | grep mResumedActivity` → 考试总览页是 `XfjfExamOverviewActivity`；③ 锁屏页只有时间/日期/知识卡片/电量，不会出题目。别把锁屏提示当考试抓拍去喊用户刷脸。

## 屏幕方向坑（浪费大量时间）

`adb shell wm size` 报的是**物理尺寸**（如 `1600x2560`），不随设备旋转变化；而 `uiautomator dump` 的 bounds 和 `screencap` 的 PNG 反映的是**当前旋转后的方向**（横屏时 PNG 可能是 2560x1600、bounds 的 x 可达 2500）。两者不一致属正常，别据此判定哪一个是错的。**唯一可靠的点击坐标来源是本次新 dump 出来的 bounds**——每次页面加载/旋转/返回后都重新 dump 取坐标，绝不跨页面、跨方向复用写死的数值。切片 OCR 的扫描范围也要用当前 PNG 的实际宽高，不要用 wm size 的物理宽高。

## 首页导航坐标会变

12123 首页出现「业务待办/参加学习教育」卡片后，原有图标位置整体下移。不要用记忆中的固定坐标点，用 OCR 逐行扫描定位，或先 `am force-stop` 重开 app 回到干净首页再按当次 dump 坐标点。

## 人脸抓拍（无法代劳，必须本人）

学习和考试都会随机触发 `com.sensetime.liveness.silent.SilentLivenessActivity`。失败显示「人脸识别失败【1:18】」+「再试一次」按钮（横屏 2560x1600 下中心约 (1280,869)；竖屏 1600x2560 下约 (800,1349)——**按当前 `wm size` 取，别记死**）。

```bash
$ADB $D shell input tap <再试一次中心x> <再试一次中心y>
# 轮询 Activity 离开 SilentLiveness 只代表"采集完成"，不代表比对通过
for i in 1 2 3 4 5 6; do
  sleep 2
  ACT=$($ADB $D shell dumpsys activity activities 2>/dev/null | grep -m1 mResumedActivity)
  case "$ACT" in *SilentLiveness*) ;; *) echo 采集完成; break;; esac
done
# 必须再读一次页面文字确认结果：可能弹出「人脸比对不通过，剩余N次」
$ADB $D shell "uiautomator dump /sdcard/e.xml >/dev/null 2>&1; cat /sdcard/e.xml" | grep -oE 'text="[^"]*(通过|不通过|剩余)[^"]*"'
```

**铁律：采集完成 ≠ 比对通过。** 离开 SilentLiveness 后若页面写「人脸比对不通过，剩余 N 次」，说明后端比对失败且有次数上限，再失败会作废本次学习/考试。

**不要替用户抢点「再试一次」**：用户不在摄像头前时点了就是浪费一次比对机会。正确顺序是——先停手、报告当前进度和剩余次数、喊用户到平板前正对摄像头；**等用户回话确认已就位**，再点「再试一次」触发采集，然后读文字确认比对结果。用户没回应就一直停着，不要反复触发。

## 看图题

- 标志/信号灯颜色题：vision 模型常无额度、百度OCR读不出颜色 → 无法可靠判断。纯文字可推理的常识题可答（如「锯齿状白色实线=可变导向车道」「行人横穿=减速让行」「夜间路口全程远光灯=错」）。
- 真正要看图才知道答案的题，交给用户答，不要让模型瞎猜——90 分及格只有 2 题容错。
- 图片裁剪法（备用）：`PIL` 裁题目下方区域，统计红/蓝像素判断标志底色（红圈=最高限速，蓝底=最低限速）。

**考试进行中图标题的秒判法（实测：补考全程按此法答完 20 题）**：主 vision 无额度、免费 vision 限流时，别再试模型——直接用 `screencap` + PIL 像素统计，1–2 秒判定，绝不占用 44 秒限时：①信号灯色——图区 y1100-1400 分别统计纯红(R>190,G<80,B<80)/纯绿(G>150,G>R+40)/纯黄像素，哪个显著多就是哪个灯（绿灯=可直行左转右转选 Y；红圈标志=会车让行选 Y）；②标志类型——红圈像素集中=会车让行/禁令，蓝底大面积多为 App 主题色勿误判；③环境明暗——图区平均亮度 <80、暗像素占比 >0.8 = 夜间/隧道，起步不能开远光；④“应注意哪些潜在危险”类多选/组合题，①②③全列通常全选。这些是通用安全原则兜底，看图题按此秒判不纠结。——实测顺序试 vision 主模型（无额度）→OpenRouter 免费 vision（llama 下架 / gemma 限流）→PIL 像素聚类，几分钟过去直接超时、整场考试失败。**开考前**必须确认一条可用通道：①题库 API（shujuyu.cn 等，¥0.002/次，题干匹配拿答案、看图题带 images URL）开考前验证可用并预取全部 20 题答案，考试时 `batch` 一次灌完；②确认 vision 模型额度有效；③都不行就开考前把看图题答案先问用户。**考试进行中**看图题若 2 秒内判不出，立即按最可能项答或跳过，绝不现场调试模型。
- 信号灯亮色定位：截屏后用**严格纯色阈值**（红灯 `R>200 & G<70 & B<70`，绿灯 `G>180 & R<90 & B<90`，黄灯 `R>210 & G>190 & B<90`）按 y/x 聚类找**孤立亮灯块**——App 主题绿色会产生上万绿色像素，宽阈值数颜色总量必误判；只认面积为几十到几百像素的孤立色块（红灯亮/另两灯灭时只有一块）。红灯→「不得越过停止线」。仍无法可靠判定就交用户目视，别猜。

## 保活设置

```bash
OLD=$($ADB $D shell settings get system screen_off_timeout)
$ADB $D shell settings put system screen_off_timeout 2147483647  # 常亮
# ...答题...
$ADB $D shell settings put system screen_off_timeout $OLD  # 结束恢复
$ADB $D shell rm -f /sdcard/s.png /sdcard/e.xml /sdcard/u.xml
```

## 锁屏解锁（用户给 PIN 后）

```bash
$ADB $D shell input keyevent 224          # 点亮（比26可靠）
$ADB $D shell input swipe 800 2100 800 700 350   # 上滑出PIN盘
$ADB $D shell input text <PIN>            # 输PIN
$ADB $D shell dumpsys trust | grep deviceLocked  # deviceLocked=0 即解锁成功
```

华为平板若默认人脸解锁且光线不足失败，上滑后会出 PIN 盘，直接 `input text` 即可。`input keyevent 82`(MENU) 会拉下通知栏并导致截图变 0 字节，用 BACK 收起即可恢复。
