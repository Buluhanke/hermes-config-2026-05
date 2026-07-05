---
name: hermes-portal-gateway-setup
description: One-command setup for Nous Portal OAuth, model selection, and Tool Gateway enabling (web search, image gen, TTS, browser, terminal). Replaces fragmented provider configurations with a unified subscription.
version: 1.0.0
author: Hermes Agent
tags: [setup, nous-portal, tool-gateway, configuration]
---

# Hermes Portal Gateway Setup Skill

## 一句话总结
`hermes setup --portal` 一键完成：Nous Portal OAuth → 选模型 → 配置 inference provider → 开启 Tool Gateway (web search/image gen/TTS/browser/cloud terminal 可选) → 直接 `hermes chat` 可用

## 为什么需要这个技能
当前常见做法：分别配置 MiniMax/Doubao/DeepSeek 等单独 provider + 各自登录对应 AI 网站获取知识，过程繁琐且易错。  
Nous Portal 统一 300+ 前沿模型 + 5 种工具网关，只需一次 OAuth 登录即可获得：
- Web search & extract (Firecrawl)
- Image generation (FAL: 9 models)
- Text-to-speech (OpenAI TTS)
- Cloud browser automation (Browser Use)
- Cloud terminal sandbox (Modal, 可选)
全部走 Nous 订阅结算，免除单独注册/充值/密钥管理。

## 前置条件
- 已安装 Hermes Agent（`hermes --version` 可用）
- 可打开浏览器完成 OAuth 流程（会自动跳转到 portal.nousresearch.com）
- 建议提前注册 Nous 订阅（首次可享免费额度），地址：https://portal.nousresearch.com/manage-subscription

## 步骤

1. **执行 setup 命令**  
   ```bash
   hermes setup --portal
   ```
   - 会打开浏览器引导完成 Nous Portal OAuth 登录
   - 登录后引导选择默认模型（推荐：先选 `Nemotron-3 Super 120B-A12B` 或 `Claude Sonnet 4.6`）
   - 自动写入 `config.yaml`：
     ```yaml
     provider: nous
     model: <你选的模型>
     ```
   - 自动开启 Tool Gateway（对应 `tool_gateway.enabled: true`）

2. **验证生效**  
   ```bash
   hermes doctor
   ```
   应该看到：
   - `Provider: Nous (configured)`
   - `Tool Gateway: enabled (web_search, image_gen, tts, browser, terminal)`

3. **立即测试对话**  
   ```bash
   hermes chat "你好，简单介绍下自己"
   ```
   应能得到流畅回复，说明模型 + 推理通路正常。

4. **可选：只开启特定网关**（如只需要搜索）  
   编辑 `config.yaml`，在 `tool_gateway` 下单独开关：
   ```yaml
   tool_gateway:
     enabled: true
     web_search: true   # 默认 true
     image_gen: false   # 暂时关闭图片生成省资源
     tts: true
     browser: true
     terminal: false    # Modal 终端沙箱默认关
   ```

## 备用方案：API Key 认证（用于 Fallback 链，无需 OAuth）

如果不需要 OAuth + Tool Gateway（仅需 Nous Portal 作为 fallback 链的 provider），可以用 API key 认证。比 OAuth 轻量，不依赖浏览器重定向。

### 步骤

1. **在 Nous Portal 创建 API Key**
   ```bash
   # 浏览器打开
   https://portal.nousresearch.com/orgs/<org-name>/api-keys
   # → 点 "Create key" → 输入名称 → 点 "Create"
   # → 页面显示 sk-nous-... 格式的 key → 点复制按钮
   ```

2. **写入 Hermes auth 池**
   ```bash
   hermes auth add nous --type api-key --api-key "sk-nous-<your-key>"
   # → Added nous credential
   ```

3. **写入环境变量**（config.yaml 引用 `${NOUS_API_KEY}`，这个 env var 必须存在）
   ```bash
   echo 'export NOUS_API_KEY="sk-nous-DNDy3A6LnS5nNxwKBY3s5WpBYJDHwFBq"' >> ~/.hermes/.env
   ```

4. **添加 Fallback 条目**（`~/.hermes/config.yaml` 的 `fallback_providers[]`）
   ```yaml
   - api_key: ${NOUS_API_KEY}
     base_url: https://inference-api.nousresearch.com/v1
     label: Nous Portal (免费 Fallback)
     model: stepfun/step-3.7-flash:free
     provider: nous
     request_timeout_seconds: 20
   ```
   **免费模型**：仅 `stepfun/step-3.7-flash:free`（Step 3.7 Flash）是零成本模型。Hermes-4 系列（70B/405B/4.3）全部付费。

5. **验证连通性**
   ```bash
   curl -s -w "\n%{http_code}" https://inference-api.nousresearch.com/v1/chat/completions \
     -H "Authorization: Bearer $NOUS_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"stepfun/step-3.7-flash:free","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
   # 期待: HTTP 200, 有 choices[0].message.content
   ```

6. **重启 gateway 生效**
   ```bash
   hermes gateway restart
   ```

### 与 OAuth 方案的区别

| 维度 | OAuth (`hermes setup --portal`) | API Key (本方案) |
|------|------|------|
| 用途 | 主 provider + Tool Gateway | fallback 链 provider |
| 依赖 | 浏览器重定向 | 纯 CLI |
| 模型数 | 全部付费+免费 | 仅免费可用（否则烧钱） |
| Tool Gateway | 附带 5 个网关 | 无网关 |
| 推荐场景 | 主力推理 | 兜底降级 |

## 常见问题 & 排错

| 问题 | 检查点 | 解决方案 |
|------|--------|----------|
| OAuth 卡在登录页 | 浏览器是否弹出 nousresearch.com 登录框 | 确认网络可达 portal.nousresearch.com；必要时打开浏览器手动访问 https://portal.nousresearch.com |
| setup 后 `hermes chat` 无响应 | `hermes doctor` 看 provider 是否为 nous | 重新运行 `hermes setup --portal` 确认选择了模型；检查 `~/.hermes/config.yaml` |
| 某个工具不可用（如搜索返回空） | `hermes doctor` 看对应网关是否显示 enabled | 打开 `config.yaml` 确认该工具开关未被误关；重新执行 `hermes setup --portal` 会恢复默认全开 |
| 想换回自己的 provider（如 MiniMax） | `config.yaml` provider 字段 | 手动改回 `provider: minimax` 或您习惯的 provider；但会失去 Tool Gateway 聚合便利性 |

## 最佳实践（血泪教训）

- **首次强烈建议用 `--portal`** ：省去 5+ 个单独服务的 API key 申请/配置/费用监控成本。
- **模型选择建议**：日常对话/代理任务用 `Nemotron-3 Super 120B-A12B`（当前环境默认）；长文档推理切 `Gemini 3 Pro`；极致速度/成本敏感用 `Haiku 4.5` 或 `GPT-5.4 Nano`。
- **网关资源权衡**：在 24GB Mac mini 上，`browser`（头less Chromium）和 `terminal`（Modal沙箱）会额外占内存/流量；如仅做文本任务，可临时关闭 `browser: false`、`terminal: false`。
- **养成习惯**：每次重大环境变动（新技能、大型任务前）先跑 `hermes doctor` 确认 portal + 网关状态正常。

## 验证清单（完成后勾选）

- [ ] `hermes setup --portal` 执行完毕且未报错
- [ ] `hermes doctor` 显示 `Provider: Nous` 和全部需要的网关 `enabled`
- [ ] `hermes chat "测试"` 能得到非空回复
- [ ] 已把此流程写入 `MEMORY.md` 作为标准作业操作（SOP）

## 与已有技能的关系
- 比 `hermes-skill-discovery` 更底层：属于环境准备阶段，先装好“发动机和油门”再去学开车（具体技能）。
- 与 `proactive-execution` 配合使用：环境就绪后 agent 可更主动地调用 `web_search`、`browser_navigate` 等网关工具执行任务。
- 为 `hermes model selection` 提供统一入口：通过 Portal 切模型无需改动凭改密钥，只改 `config.yaml` 中 `model` 字段。

## 一句话闭环
**装了这个 skill = 下次新设备或重装系统时，一条命令恢复完整推理 + 5 大工具能力，开箱即用。