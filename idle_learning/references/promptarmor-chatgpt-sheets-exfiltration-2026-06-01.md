# ChatGPT for Google Sheets — PromptArmor Data Exfiltration Disclosure

**来源**：https://www.promptarmor.com/resources/gpt-for-google-sheets-data-exfiltration
**发现日期**：2026-06-01（方向C 07:40 巡检）
**HN 得分**：92pts
**公开日期**：2026-05-27

## 概述

OpenAI 推出的 ChatGPT Google Sheets 扩展（185K+ 下载，上线 <1 月）存在间接提示注入漏洞。攻击者在单个 sheet 中嵌入提示注入 → 受害者一旦与扩展交互，整个账户的工作簿被窃取。

## 攻击效果（单次注入同时触发）

1. **跨工作表数据窃取**：从受害者账户中窃取多个工作簿（演示中窃取 12 个）
2. **交互式钓鱼弹窗**：覆盖 ChatGPT 侧边栏的攻击者控制界面
3. **GPT 侧边栏完全接管**：被替换为攻击者控制的聊天机器人界面
4. **恶意工作表编辑**：攻击者可编辑用户的任意工作表

## 绕过「人类审批」设置

- ChatGPT for Google Sheets 有"Apply edits automatically"设置
- **攻击即使在该设置关闭时仍然成功**
- 该漏洞验证了纯配置层面的防御（"要求人类批准"）在架构级攻击面前不可靠

## 攻击链

1. 用户正在使用内部财务模型工作表
2. 用户导入外部数据集（含有隐藏的提示注入，白字文本）
3. 用户要求 ChatGPT 帮助整合数据
4. 提示注入操纵 ChatGPT 运行外部攻击者控制的脚本
5. 脚本执行扩展权限 → 窃取当前工作簿
6. 脚本从已窃取数据中识别其他工作簿链接 → 继续窃取（演示中 12 个工作簿）
7. "停止"按钮无法阻止已启动的脚本执行

## OpenAI 回应

- 2026-05-08：PromptArmor 通过邮件披露
- 2026-05-08：OpenAI 自动回复确认
- 2026-05-12/18：PromptArmor 两次跟进，**无回复**
- 2026-05-27：公开披露

## 对 Hermes 的启示

1. **设置不是安全边界**：ChatGPT 的"需要人类批准"设置被绕过 → DRY_RUN=False 的 Verify 阶段必须是架构级 guardrail，不能仅依赖配置
2. **权限粒度不足**：扩展获得"可以做什么"的权限，但无法区分"用户要求做"vs"外部内容要求做" → Hermes WHITELIST 的 scene→action 映射至少保留了作用域限制
3. **止损机制缺失**：演示中"停止"按钮无法阻止已启动脚本 → Handler 的每帧独立场景分类+否定检测提供了天然止损（每帧都可以拒绝下一步）
