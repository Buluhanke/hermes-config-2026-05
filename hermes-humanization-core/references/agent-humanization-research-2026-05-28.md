# 真人化研究方向（2026-05-28）

## 四大维度

### ① 操作轨迹拟真
- 鼠标移动：贝塞尔曲线+随机抖动，不用直线
- 打字节奏：随机延迟50-150ms/字
- 滚动：分段+不定速
- 工具：undy、pyautogui延迟层、humanize-rs

### ② 浏览器指纹隐匿
- Canvas/WebGL/Audio指纹随机化
- 时区/语言/UA跟随系统
- IP代理轮换
- 工具：undetected-chromedriver、selenium-stealth、multilogin

### ③ 屏幕全域感知（当前卡点）
- 视觉识别验证码、弹窗、UI变化
- 方案：Qwen2-VL / Apple Vision OCR + 屏幕diff检测
- 移动端模拟（iOS/Android真机或模拟器）

### ④ 行为随机化
- 操作前随机停顿1-3秒
- 不完美的点击目标（±5px偏移）
- 不固定的操作顺序

## 现状差距（2026-05-28）
- ✅ 鼠标轨迹已有基础（cua-driver）
- ❌ 浏览器指纹未处理
- ❌ 验证码识别未解决
- ❌ 移动端完全空白

## 研究方法备注
- Firecrawl搜索需要付费额度，额度耗尽时直接走浏览器或curl
- 代理（HTTP_PROXY=http://127.0.0.1:1082）可能未运行，curl走代理返回exit:7
- 国内网络建议用百度/huggingface镜像，绕过GFW