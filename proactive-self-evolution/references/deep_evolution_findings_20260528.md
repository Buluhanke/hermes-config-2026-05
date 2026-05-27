# 深度进化发现汇总 | 2026-05-28 02:00

## 屏幕感知工具（最高优先，24k+ stars级别）

### OmniParser (Microsoft) — 24,812★
- **URL**: https://github.com/microsoft/OmniParser
- **核心能力**: 纯视觉GUI解析器，把截图变成结构化可交互元素
- **关键数据**: V2版本 ScreenSpot Pro grounding 准确率 **39.5%**，支持 GPT-4V/Claude/DeepSeek/Qwen2.5VL
- **HuggingFace**: microsoft/OmniParser-v2.0, microsoft/OmniParser-v1.5
- **真人化价值**: ★★★★★ 最高，直接解决 Hermes 屏幕感知短板

### Agent-S (Simular AI) — 11,658★
- **URL**: https://github.com/simular-ai/Agent-S
- **核心能力**: 首个在 OSWorld 基准上超越人类的计算机操作 Agent（72.60%），跨平台（macOS/Win/Linux），in-context强化学习+记忆
- **真人化价值**: ★★★★★ 最高，有云端版可直接试用

### CUA Driver (trycua) — 17,136★
- **URL**: https://github.com/trycua/cua
- **核心能力**: macOS 后台计算机操作 agent，**不抢光标/不抢焦点/不跳Space**，可操作非AX表面
- **真人化价值**: ★★★★ 高，安装命令：
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"
  ```

### MobileAgent (Alibaba) — 8,744★
- **URL**: https://github.com/X-PLUG/MobileAgent
- **核心能力**: GUI agent 家族，多模态，支持桌面/移动端

---

## 反爬隐身浏览器（解决验证码/反爬问题）

### CloakBrowser — 21,717★
- **URL**: https://github.com/CloakHQ/CloakBrowser
- **核心能力**: 30/30 反机器人检测通过，`humanize=True` 类人操作，reCAPTCHA v3 分数 **0.9**
- **技术**: 58个C++层源码补丁（canvas/WebGL/音频/字体/GPU/WebRTC等）
- **接入**: `pip install cloakbrowser`，3行代码30秒
- **真人化价值**: ★★★★★ 最高，**1688采购最大突破口**

### Botright — 990★
- **URL**: https://github.com/Vinyzu/Botright
- **核心能力**: fingerprint 变换 + 免费 AI captcha 解决，Built on Playwright

### patchright — 3,312★
- **URL**: https://github.com/Kaliiiiiiiiii-Vinyzu/patchright
- **核心能力**: Playwright 隐形版，Python/TypeScript 双版本

---

## 快速测试命令

```bash
# CloakBrowser 测试（无需安装）
docker run --rm cloakhq/cloakbrowser cloaktest

# CUA Driver 安装
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"

# OmniParser（需 GPU，M4 可能不够）
pip install omniparser
# 或 Docker
docker run -p 8332 ghcr.io/microsoft/omniparser
```

---

## 推荐整合架构

```
Hermes 核心
    ↓
CloakBrowser（隐身浏览器层） → 绕过1688反爬/验证码
    ↓
OmniParser（屏幕感知层） → 视觉→结构化元素
    ↓
CUA Driver（后台操作层） → 不干扰用户的后台执行
    ↓
现有 MCP/1688自动化能力 → 业务闭环
```

---

*由 Hermes 深度进化系统 | 2026-05-28T02:00*