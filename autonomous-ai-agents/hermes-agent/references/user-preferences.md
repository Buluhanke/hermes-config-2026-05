# 用户偏好汇总（本机 mac / aimac）

## 交互风格
- 偏好直接执行不啰嗦，不要 step-by-step 指导，直接做。
- 用户主动说"不用了"时立即停止。
- 系统提示（command approval、error、warning 等）必须用中文显示，不能用英文。
- 不希望看到模型调用失败和 fallback 的详细技术提示（如 API call failed, switching to fallback 等），偏好默默切换模型。
- **通知精简**：讨厌"无聊的信息通知"，不希望看到工具进度条、中间消息、完成提示等杂音。应将 `display.tool_progress` 设为 `minimal`，`display.interim_assistant_messages` 设为 `false`，`display.compact` 设为 `true`。

## 铁律（非偏好，必须遵守）
- **配置/删除模型时绝对不能动通讯渠道**（QQ、企业微信等）。通讯渠道独立于模型配置，互不影响。  
- **不要擅自添加平台监控定时任务**。用户认为正常配置好的 credentials 不会自动丢失或失效，不需要 cron 定时检查。添加 cron 前必须事先询问。

## 模型偏好（2026-05-16 更新）
- **当前模型链**：
  1. 默认 → custom:V2.aicodee.com → MiniMax-M2.7-highspeed（中转）
  2. 备用 → minimax-cn → MiniMax-M2.7（国内直连）
  3. 压轴 → deepseek → deepseek-v4-flash
- `/model` slash command 可用（不再需要重启 gateway 切换）
- 修改 config 后，当前 session 不生效，需要 `/new` 或重启
- .env 会覆盖 config.yaml（如 MINIMAX_CN_BASE_URL 覆盖 model.base_url）
- 修 endpoint 必须同时改 config.yaml 和 .env，单改一个不生效

## 业务偏好
- 采购偏好：纸箱等包装材料采购，产地尽量控制在江浙沪地区，候选供应商最少 10 个。
- 使用 supply-agent-v11 做供应链找品，通过企业微信（WeCom）和 QQ 两个渠道与 Hermes 对话。企业微信 Bot ID=aibRODF-ClY8HEBFS1Zu_aNcXH3WCmeYfMK。
- 1688 爬虫项目在 ~/1688_bot/，目前被 1688 反扒完全阻止（返回虚假 HTML），Playwright 所有方案均失败。需要换用 Selenium 或换平台（拼多多/淘宝）验证逻辑。Chrome Profile 在 ~/chrome_profile/，login.json 已有但对 1688 无效（cookie 是加密的）。

## 已知问题
- vision_analyze 在本系统不稳定，截图发给用户后经常报告"无法看到图片"。处理用户发的图片时优先尝试保存到本地文件路径（`/tmp/`）再分析。
- 1688 反扒极严，Playwright 自动化完全被检测并返回虚假 HTML，需换 Selenium 或换平台。

## Clash 代理直连域名
- 国内 AI 模型 API 必须绕过 Clash 代理直接连接，否则延迟显著增加（~5.7x）或完全不可用。
- 直连域名列表（已配置到 clash-verge.yaml 的 rules 段）：
  - `DOMAIN-SUFFIX,aicodee.com` — MiniMax Relay
  - `DOMAIN-SUFFIX,deepseek.com` — DeepSeek API
  - `DOMAIN-SUFFIX,localhost` — 本地 Ollama
  - `DOMAIN,127.0.0.1` — 本地服务
- 修改方式：编辑 `~/.config/clash-verge-rev/clash-verge.yaml`（或 macOS Application Support 目录下的同名文件），在 rules 段顶部添加上述规则，指向 `🎯 全球直连` 策略组。修改后 `killall -HUP clash-verge` 热重载。
