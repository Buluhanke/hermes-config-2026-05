# Screen Understanding 免费本地方案（2026-05-14 研究）

## 两条并行路线

### 路线A：AI/VLM 路线（依赖模型推理）
- **ChatGPT CUA** (OpenAI) — 要付费
- **Claude computer use** — 要付费
- **Qwen3-VL + browser-use + Ollama** — 完全免费，本地运行，Reddit 评为开源最强屏幕理解 VLM

### 路线B：纯技能/插件路线（不依赖大模型 API）
- **Fazm AI** — macOS 原生，语音+屏幕理解，100%本地，开源免费
- **Taskhomie** — 本地截图+模型控制鼠标键盘
- **n8n 自托管** — 工作流自动化+AI节点，100%本地Docker
- **browser-use** — Playwright驱动，可用Ollama本地模型，开源免费
- **open-computer-use** — AI控制Windows/Mac电脑，类似ChatGPT Operator

## 最佳免费组合（用户首选）

**Qwen3-VL + browser-use + Ollama**

- Qwen3-VL：Reddit 社区测试为开源最强屏幕理解视觉模型
- browser-use：开源浏览器自动化框架，AI只负责理解"点哪里"
- Ollama：本地跑模型，完全不依赖 API key
- 流程：截图 → Qwen3-VL判断"这是搜索框，该点这里" → browser-use 执行

## 不依赖大模型的方向

1. **规则 + OCR** — PaddleOCR等开源OCR识别文字坐标，规则匹配点击位置。缺点无语义理解。
2. **AXUI（无障碍API）** — macOS Accessibility框架直接读UI树，拿到元素坐标和角色。Hermes现有架构在用。
3. **CV视觉定位** — OpenCV模板匹配找按钮，需要事先有模板。

## 相关资源

- https://github.com/browser-use/browser-use — 开源，Ollama可本地运行
- https://github.com/niuzaisheng/ScreenAgent — VLM驱动计算机控制
- https://github.com/suitedaces/computer-agent — Taskhomie，本地AI agent
- https://fazm.ai — macOS原生桌面Agent
- https://www.reddit.com/r/LocalLLaMA/comments/1pmn mpb/best_opensource_vision_model_screen — Qwen3-VL评价
- https://github.com/ranpox/awesome-computer-use — Computer Use Agent资源汇总

## 在 Mac mini M4 (24GB) 上的可行性

- Ollama 可本地运行 Qwen3-VL
- browser-use + Ollama 组合完全免费
- Fazm AI 是 macOS 原生方案，值得测试

## 实际测试结果（2026-05-14）

**已安装并验证可用**：`ahmadwaqar/smolvlm2-agentic-gui`
- 大小：2.0GB（两个chunk文件：1.1GB + 872MB）
- 特点：专门微调过GUI自动化，直接输出 `click(x=0.519, y=0.238)` 归一化坐标
- 安装命令：`ollama pull ahmadwaqar/smolvlm2-agentic-gui`
- 验证：截1688首页发给模型 → 回复 "选择搜索页面中的纸箱供应商链接" + `click(x=0.519, y=0.238)`
- 内存占用：推理时约3-4GB，完全在24GB Mac mini承受范围内

**调用方式**：
```python
# 用 /api/generate，不是 /api/chat
# prompt里加 <image> 表示图片位置
import requests, base64

with open("/tmp/screen.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "ahmadwaqar/smolvlm2-agentic-gui",
    "prompt": "这是网页截图，告诉我应该点击哪个链接？用中文简短回答，只说点击什么元素。<image>",
    "images": [img_b64],   # 注意是 images 数组，不是 content 里的 image_url
    "stream": False
}
resp = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=60)

# 解析归一化坐标
import re
m = re.search(r'click\(([\d.]+),\s*([\d.]+)\)', resp.json().get("response", ""))
if m:
    # 屏幕分辨率 1920x1080
    x_actual = int(float(m.group(1)) * 1920)
    y_actual = int(float(m.group(2)) * 1080)
```

**已知坑**：
- MiniMax 的 vision API 不支持 `image_url` 格式（报错 `unknown variant image_url`）
- `browser_vision` 工具底层用 MiniMax，需用 Ollama 本地模型做 vision fallback
- 获取屏幕分辨率：`system_profiler SPDisplaysDataType | grep Resolution` → `1920 x 1080 @ 60.00Hz`
