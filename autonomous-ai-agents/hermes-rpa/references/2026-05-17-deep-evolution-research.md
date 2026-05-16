# 深度进化研究摘要 — 2026-05-17 02:00

## 执行情况
- 全网搜索：4个方向（屏幕感知/验证码/类人节奏/1688采购）
- 浏览器AI对话：CDP WebSocket沙盒隔离阻塞，未完成
- 文档归档：Vision_Lab + Brain_Lab 各1份

---

## 屏幕感知突破（最优先）

### 行业格局 2026

| 方案 | 公司 | 能力 | 开源 | 备注 |
|------|------|------|------|------|
| Anthropic Computer Use | Anthropic | 87% WebArena | 闭源 | Claude 3.5/3.7 |
| OpenAI CUA | OpenAI | 58% WebArena, 38% OSWorld | 闭源 | GPT-4o视觉+RL |
| Google Mariner | Google | 84% ScreenSpot, 83.5% WebVoyager | 闭源 | Gemini 2.0 |
| **browser-use** | 开源 | 78k stars | ✅开源 | Python+LLM, DOM→action |
| ShowUI | 浙大 | VLA模型, GUI grounding | 论文 | CVPR 2025 |
| **Aria-UI** | ACL 2025 | 纯视觉grounding, SOTA | 论文 | arxiv.org/abs/2412.16256 |

### browser-use (78k stars)
- GitHub: browser-use/browser-use
- Python库，LLM控制浏览器，DOM→LLM→action完整闭环
- 支持本地Ollama模型，免费开源
- 核心思路：不同于CDP AXTree，browser-use用DOM + LLM理解页面结构

### smolvlm2 (Ollama已装)
- `ahmadwaqar/smolvlm2-agentic-gui` (2GB, Mac本地可跑)
- 微调过直接输出归一化坐标 `click(x=0.519, y=0.238)`
- 比Baidu OCR语义理解强，成本¥0

---

## 验证码对抗（最高优先，卡点1688）

### 2025年CAPTCHA格局
- reCAPTCHA v3, hCaptcha, Cloudflare Turnstile → 行为分析，不只是图灵测试
- 检测维度：指纹 + 行为 + IP + 会话特征

### 主要方案对比

| 方案 | 类型 | 成功率 | 成本 | 备注 |
|------|------|--------|------|------|
| Skyvern | 集成平台 | 85%+ | $16/mo+ | 生产级 |
| Anti-Captcha | 人工打码 | 99% | 按题计费 | 高价值目标 |
| **CapSolver** | AI识别 | 60-80% | 按题计费 | 标准CAPTCHA首选 |
| **Patchright** | 反指纹 | 40-60% | 免费 | Playwright fork |
| Stealth插件 | 浏览器修改 | 40-60% | 免费 | **2025已无效** |

### Patchright (已装，重要！)
- CLI: `/Library/Frameworks/Python.framework/Versions/3.14/bin/patchright` (v1.58.2)
- Python包: pip安装后是 `import patchright`（与playwright API兼容）
- Playwright drop-in替代，反指纹硬化
- 对Cloudflare Turnstile效果有限，辅助方案非主方案

### CapSolver API
- 注册: capsolver.com
- 标准reCAPTCHA/hCaptcha/图像验证码识别
- 1688滑动验证码：预估0.1-0.5元/题
- 需要实测1688验证码类型（非标准reCAPTCHA）

### 1688特殊性
- 阿里巴巴自研验证码系统，非标准reCAPTCHA
- **扫码登录（手机阿里APP）比账号密码更稳定**
- 滑动验证：hermes-rpa已有overshoot+回退技术

---

## 类人操作节奏

### 关键技术
- 鼠标轨迹贝塞尔曲线（非直线）
- 打字节奏随机化（非均匀延迟）
- 浏览器指纹随机化（Canvas, WebGL, Audio）
- 页面停留时间模拟

### Hermes现状
hermes-rpa已有：基础随机延迟、缓动函数（但click.py未集成）
缺失：贝塞尔轨迹、打字节奏模块、指纹硬化

### 行动项
- [ ] 集成贝塞尔鼠标轨迹到 `perception/actions/click.py`
- [ ] 新增humanization模块
- [ ] FingerprintJS等免费库评估

---

## 1688采购闭环

### 可行方案对比

| 方案 | 成本 | 登录态 | 风险 |
|------|------|--------|------|
| CDP持久化Chrome | 免费 | ✅ | 低(反爬升级) |
| 人工+API混合 | 低 | ✅ | 中 |
| CapSolver打码 | ¥50-500/月 | ✅ | 低 |
| 第三方采集服务 | $50+/月 | ✅ | 依赖外部 |

### 卡点优先级
1. **验证码** ← 最高优先
2. **反爬升级** (2025年1688加强)
3. **供应商谈判** (需要真人)
4. **订单处理** (1688无API)

---

## 本周最高价值行动

1. **(最优先) CapSolver注册 + 1688验证码实测** — 解除1688采购闭环卡点
2. **(次优先) smolvlm2 + 1688页面实战** — 感知从¥0.003/次→免费
3. **(第三) Patchright测试** — `patchright --help` 立即可用

---

## 存疑（需用户确认）

1. CapSolver付费意愿（按题计费，量大月¥50-500）
2. Patchright测试期间Chrome需重启
3. 1688账号CDP方案是否有被封风险（无明确条款但有风险）
