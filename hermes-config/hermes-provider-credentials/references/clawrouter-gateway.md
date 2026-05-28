# ClawRouter API 网关

## 平台概况

**ClawRouter** (https://clawrouter.com) 是一个统一 LLM API 网关服务，支持 OpenAI 兼容格式。提供 111+ 模型、11+ 供应商接入能力。

**注意**：ClawRouter 是**云服务**（非本地工具），需注册获取 API Key 使用。

## 与实际网站差异

用户原始描述称 ClawRouter "无需API key，通过钱包签名认证，本地<1ms智能路由，USDC按次支付"。

**实际网站 clawrouter.com 显示**：
- ✅ **需要 API Key**（格式 `YOUR_API_KEY-...`），需注册账号获取
- ✅ **OpenAI 兼容** — 改 `baseURL: https://clawrouter.com/v1` 即可
- ❌ 支付走 **Stripe**，非 USDC/钱包
- ❌ 是**云服务**，非本地路由器
- 模型：111+，供应商：11+

→ 教训：**不要盲信第三方对 LLM 路由服务的描述**。先访问官网验证再配置，避免基于错误假设安装。

## 接口信息

| 项目 | 值 |
|------|-----|
| Base URL | `https://clawrouter.com/v1` |
| API Key 格式 | `YOUR_API_KEY-...` |
| API 兼容 | OpenAI (Chat Completions) |
| 文档 | https://clawrouter-api.gitbook.io/clawrouter/ |
| 定价 | 按量付费 (Stripe) |
| GitHub | https://github.com/clawrouter（无公开仓库） |

## 支持的模型（部分）

| 模型 | 供应商 | 输入价格 | 输出价格 | 上下文 | 功能 |
|------|--------|---------|---------|--------|------|
| claude-opus-4-1-20250805 | Anthropic | $5/M | $25/M | 200K | vision/tools/stream |
| claude-opus-4-20250514 | Anthropic | $5/M | $25/M | 200K | vision/tools/stream |
| claude-opus-4-6 | Anthropic | $5/M | $25/M | 1M | vision/tools/stream |
| claude-opus-4-7 | Anthropic | $5/M | $25/M | 1M | vision/tools/stream |
| gpt-5.4 | OpenAI | $5/M | $22.5/M | 1M | vision/tools/stream |
| gpt-5.3-codex | OpenAI | $1.75/M | $14/M | 512K | tools/stream |
| gpt-5.5 | OpenAI | $2.5/M | $20/M | - | - |
| gemini-3.5-flash | Google | $0.6/M | $3.6/M | - | - |
| gemini-3.1-pro | Google | $4/M | $18/M | 1M | vision/tools/stream |

## Hermes 配置要点

### 作为 custom provider 添加

```yaml
custom_providers:
  - api_key_env_var: CLAWROUTER_API_KEY
    base_url: https://clawrouter.com/v1
    model: claude-opus-4-7
    name: clawrouter
```

### credential_pool_strategies

```yaml
credential_pool_strategies:
  custom:clawrouter: fill_first
```

### .env 配置

```
CLAWROUTER_API_KEY=YOUR_API_KEY...
```

## 与 v2.aicodee.com 对比

| 特性 | ClawRouter | v2.aicodee.com |
|------|-----------|----------------|
| 模型数 | 111+ | 30+ 供应商 |
| 支付 | Stripe 直接充值 | 第三方中转套餐 |
| 主打 | 全线大模型（Claude/GPT/Gemini） | MiniMax + 国内模型 |
| 文档 | GitBook | 无正式文档 |
| Key 获取 | 官网注册 | 第三方购买 |
