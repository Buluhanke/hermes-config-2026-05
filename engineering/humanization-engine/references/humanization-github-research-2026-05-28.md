# 真人化GitHub研究成果 (2026-05-28)

## 搜索方式
- GitHub API via curl: `https://api.github.com/search/repositories?q={keywords}&sort=stars&per_page=6`
- 代理端口：**必须用7897**（Clash），1082是Shadowrocket端口（不通）

## ⭐⭐⭐⭐⭐ 优先落地：鼠标轨迹

### WindMouse（⭐56，GPLv3，pip可装）
- Python库，实现WindMouse算法——贝塞尔曲线+速度变化，模拟人手移动惯性
- 支持：AutoHotkey(Windows) + PyAutoGUI(跨平台)
- 用途：替换直线跳跃式鼠标移动
- 安装：`pip install windmouse`
- README摘要："generates curved, natural-looking paths instead of straight lines, varying movement speed dynamically throughout the trajectory"
- 使用：
```python
from windmouse import wind_mouse
wind_mouse(start_x, start_y, dest_x, dest_y, move_gen=lambda p1, p2: ... )
```

### Perlin-Mouse-Simulator（⭐1）
- Perlin噪声生成鼠标轨迹，更高级
- Python+Tkinter GUI

---

## ⭐⭐⭐⭐ 重点：反浏览器检测

### SeleniumBase（⭐12743，Python）
- CDP Mode过所有主流bot检测，包括Cloudflare
- 集成了E2E Testing + CAPTCHA-bypass + Playwright
- 主题：anti-detection, bot-detection, playwright, pytest
- **适合Hermes**：Python+CDP，可以集成到browser CDP层

### Camofox-browser（⭐5910）
- "Stealth headless browser for AI agents — bypass Cloudflare, bot detection, anti-scraping. Drop-in"
- 专门给AI agent设计，Firefox分支
- **已知问题（macOS 26.4.1）：** binary v135.0.1-beta.24启动挂起

### CthulhuJs（⭐34）
- 浏览器指纹混淆框架（Canvas/WebGL/WebRTC）
- **注意**：⭐低但方向对

### ghost-browser（⭐2）
- TypeScript stealth layer for Puppeteer/Playwright，"makes your automation behave like a real human"

---

## ⭐⭐⭐⭐⭐ 桌面接管基础设施

### CUA（⭐17201，HTML/TypeScript）
- **Open-source Computer-Use Agents基础设施**
- Sandboxes + SDKs + benchmarks
- 支持：macOS / Linux / Windows 全桌面控制
- 主题：computer-use, computer-use-agent, containerization, cua, desktop-automation
- **这是Hermes的终极目标参照**

### computer-agent（⭐643）
- Desktop app to control your computer with AI
- 终端+浏览器+鼠标键盘

### usecomputer（⭐291）
- Fast computer automation CLI for AI agents
- 截图+点击+打字+滚动

---

## ⭐⭐⭐ 验证码识别

### Captcha-Sonic Extension（⭐30）
- AI-powered CAPTCHA solver browser extension
- 支持：Selenium, Puppeteer, Playwright

### greekr4/playwright-bot-bypass（⭐147）
- Claude Code skill，跳过Google CAPTCHA

---

## 搜索结论

| 方向 | Top项目 | 可用性 |
|------|---------|--------|
| 鼠标轨迹 | WindMouse ⭐56 | ✅ pip直接装 |
| 反浏览器检测 | SeleniumBase ⭐12743 | ✅ Python+CDP |
| 桌面接管 | CUA ⭐17201 | ⚠️ 参考架构 |
| 验证码 | Captcha-Sonic ⭐30 | 待验证 |
| 移动端 | （未搜到高星）| ❓ |

---

## 立即可落实（本周）

1. `pip install windmouse` → 接管鼠标轨迹层
2. 浏览器UA/Canvas/时区指纹随机化
3. 操作延迟+随机停顿注入