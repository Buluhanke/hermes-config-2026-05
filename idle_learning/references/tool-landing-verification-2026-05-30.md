# 工具落地实测结论 2026-05-30

## 背景
学习任务落地化：把工具真正跑通，而不是只Research不落地。

## NopeCHA SDK

**安装**：`pip install nopecha`（hermes-agent venv）

**实测**：
```python
from nopecha.api._base import APIClient
# API需要key，免费额度仅插件
# 支持类型：recaptcha, hcaptcha, funcaptcha, textcaptcha, awscaptcha
```

**结论**：
- 免费tier：Chrome插件100次/天，**不能**通过API调用
- API调用需要付费credits
- **1688阿里自研滑块不在支持列表中**（NopeCHA只支持标准CAPTCHA）
- 放弃用于1688验证码

**注册地址**：nopecha.com（从dashboard获取API key）

---

## Agent TARS CLI

**安装**：`npm install -g @agent-tars/cli`

**实测**：
```
/Users/aimac/.local/bin/agent-tars
版本：0.3.0
```
- Node.js版CLI，支持local/browsing operator
- 需要配置VLM后端（Ollama/MiniMax等）
- 架构：vision→action→verify循环，与hermes-rpa一致
- 核心能力与UI-TARS Desktop相同，可替代Desktop版

**结论**：✅ 已就绪可用，配置VLM后端即可测试

---

## patchright

**安装**：`pip install patchright`

**实测**：
```python
from patchright.sync_api import SyncPlaywright
# greenlet+asyncio pipe transport架构
# headless launch失败：SyncBase.__init__() missing impl_obj
```

**结论**：❌ greenlet/pipe transport与当前环境不兼容，放弃

---

## DrissionPage

**安装**：`pip install DrissionPage`（hermes-agent venv）

**实测**：
```python
from DrissionPage import ChromiumPage
page = ChromiumPage()
page.get('https://www.1688.com/')
# 成功加载，标题："阿里1688首页"
# 无id=nc-1-n1z滑块（首页无需验证码）
# 发现3个iframe（1688流量分析相关）
```

**结论**：✅ 可用，成功驱动Chromium访问1688
- 1688首页无需验证码
- 登录页会有滑块验证码
- ali_captcha项目（DrissionPage实现，成功率~50%）可参考

---

## playwright（官方）

**安装**：`playwright install chromium`

**实测**：chromium_headless_shell 148.0.7778.96 已下载

**结论**：✅ 官方headless正常可用，patchright有架构问题

---

## UI-TARS Desktop

**现状**：
- GitHub release无macOS预编译.dmg包（只有Linux/Windows）
- GitHub直连下载超时（github.com被blocked）
- Homebrew无此cask

**替代方案**：Agent TARS CLI（已安装）

**结论**：❌ Desktop版无法安装，用CLI替代

---

## 1688验证码实测

**首页**：`https://www.1688.com/` — 无验证码（HTTP 200正常）
**登录页**：`https://login.1688.com/member/sign-in.htm` — 有滑块
**商品详情页**：需进一步测试

**ali_captcha项目**（DrissionPage实现）：
- 成功率~50%
- 参考价值高：滑块缺口检测+滑动轨迹模拟
- 仓库：github.com/1078769434/ali_captcha

---

## 工具优先级总结

| 优先级 | 工具 | 状态 | 行动 |
|--------|------|------|------|
| P0 | Agent TARS CLI | ✅可用 | 配置VLM后端并测试 |
| P0 | DrissionPage | ✅可用 | 深入1688商品页测试验证码触发 |
| P1 | NopeCHA | ⚠️有限 | 注册API测试标准CAPTCHA（1688不适用） |
| P1 | playwright | ✅可用 | 作为browser自动化备选 |
| P2 | patchright | ❌放弃 | 架构不兼容 |
| P2 | UI-TARS Desktop | ❌放弃 | 无macOS包 |