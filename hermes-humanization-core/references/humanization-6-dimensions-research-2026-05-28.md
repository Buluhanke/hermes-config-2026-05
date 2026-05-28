# 真人化六维度调研参考（2026-05-28）

## 方向一：鼠标轨迹真人化

### WindMouse ⭐56
- 官网：https://github.com/AsfhtgkDavid/windmouse
- 算法：WindMouse（重力+风力+阻尼），生成45-80个曲线点
- 安装：`pip install windmouse`
- 依赖：numpy ✅ 已满足
- API：
```python
from windmouse.core import wind_mouse
for x, y in wind_mouse(start_x, start_y, dest_x, dest_y):
    pyautogui.moveTo(x, y)
```
- 已验证可用（2026-05-28）：100步距离→45个曲线点

### Perlin Mouse ⭐（研究方向）
- 算法：Perlin噪声生成更自然的随机轨迹
- 待研究实现

---

## 方向二：反浏览器检测

### SeleniumBase ⭐12743（Python）
- 官网：https://github.com/seleniumbase/SeleniumBase
- 核心：CDP模式，绕过所有主流bot检测
- 集成Playwright，Python自带
- 注意：重量级E2E测试框架，单独使用偏重

### CloakBrowser ⭐（研究方向）
- 官网：https://github.com/CloakHQ/CloakBrowser
- 对应Python包：`pip install cloakbrowser` ✅ 已安装0.3.30
- 核心功能：source-level fingerprint patches，drop-in playwright替代品
- 子模块：
  - `cloakbrowser.human` — 真人化操作（human_click, human_type, human_move）
  - `cloakbrowser.geoip` — IP地理位置解析
  - `cloakbrowser.config` — 指纹配置
- CDP Chrome注入已验证（2026-05-28）：成功，不影响登录态

### CthulhuJs ⭐34
- 官网：https://github.com/shawn-li-zh/CthulhuJs
- 功能：浏览器指纹混淆和 masquerading
- 特色：hook式注入，不修改浏览器本身

---

## 方向三：算子拟人化（已集成到CloakBrowser）

CloakBrowser HumanConfig 参数：
- `typing_delay: 70` / `typing_delay_spread: 40` — 打字随机延迟ms
- `mistype_chance: 0.02` — 打错字概率（2%），打错后100-300ms纠正
- `mouse_steps_divisor: 8` — 鼠标曲线路径分8段
- `mouse_min_steps: 25` / `mouse_max_steps: 80` — 鼠标路径最小/最大步数
- `idle_between_actions: True` — 操作间随机停顿0.3-0.8秒
- `scroll_delta_base: (80, 130)` — 滚动分段

---

## 方向四：全屏感知（验证码识别）

### smolvlm2（已装本地）
- 模型：`ahmadwaqar/smolvlm2-agentic-gui:latest`
- 用途：截图→VLM→坐标，识别验证码图形/滑块
- 状态：已装但未测试验证码识别能力

### 百度OCR（已装）
- 用途：文字识别（发票、截图文字）
- 缺口：图形验证码（滑块、点选、推理验证码）

---

## 方向五：移动端（已取消）

---

## 方向六：语音真人化

### Moss-TTS-Nano（已配置）
- 音色：Xiaoyu，已配
- 缺口：情感控制、停顿拟真、口语化

### Edge TTS（备用，已装）
- 音色：zh-CN-XiaoxiaoNeural（女声）
- 质量比Moss高，但需联网