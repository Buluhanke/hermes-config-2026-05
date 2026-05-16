# MiniMax 内置Provider配置

## 背景

Hermes Agent 有 3 个内置 MiniMax provider（在 `plugins/model_providers/minimax/__init__.py` 定义）：

| Provider 名 | 别名 | base_url | API模式 | 默认模型 | 环境变量 |
|---|---|---|---|---|---|
| `minimax` | mini-max | https://api.minimax.io/anthropic | anthropic_messages | MiniMax-M2.7 | MINIMAX_API_KEY |
| `minimax-cn` | minimax-china, minimax_cn | https://api.minimaxi.com/anthropic | anthropic_messages | MiniMax-M2.7 | MINIMAX_CN_API_KEY |
| `minimax-oauth` | minimax_oauth, minimax-oauth-io | https://api.minimax.io/ | OAuth 浏览器流 | MiniMax-M2.7-highspeed | (无，存 auth.json) |

## 常见问题：内置Provider配了但连不上

### 症状
- 在 config.yaml 里 `providers.minimax-cn` 配好了 api_key
- 但切换到这个 provider 后 API 调用失败

### 根因：两个东西都要配

1. **config.yaml** 的 `providers` 段
2. **.env** 里的对应环境变量

**只配一个是不够的。** Hermes 的 provider 加载机制是双层校验。

### 正确配置步骤

#### 1. config.yaml
```yaml
providers:
  minimax-cn:
    api_key: YOUR_API_KEY-xxx...xxx
```

#### 2. .env
```
MINIMAX_CN_API_KEY=YOUR_API_KEY-xxx...xxx
```

### 陷阱：BASE_URL 被覆写了

`.env` 里如果有 `MINIMAX_CN_BASE_URL`，会覆盖内置的 `https://api.minimaxi.com/anthropic`。

**如果之前用过 aicodee 中转**，往往会有：
```
MINIMAX_CN_BASE_URL=https://v2.aicodee.com/v1
```
这条的副作用是 minimax-cn provider 实际走的是中转而非直连。要切换回直连必须 **注释掉或删除** 这一行。

**判断当前用哪个 URL：**
```bash
grep "MINIMAX_CN_BASE_URL\|MINIMAX_API_KEY" ~/.hermes/.env
```

### 推荐配置（双路线并行）

```yaml
# config.yaml
model:
  default: MiniMax-M2.7-highspeed    # 主力走aicodee中转(高速)
  provider: custom                    # → aicodee custom provider
  base_url: https://v2.aicodee.com/v1
  api_key: YOUR_API_KEY...24ea

providers:
  minimax-cn:                         # 备用走MiniMax直连
    api_key: YOUR_API_KEY-...xxx

fallback_providers:
  - minimax-cn                        # 主力挂了自动切到直连
```

```bash
# .env
MINIMAX_CN_API_KEY=YOUR_API_KEY-xxx...xxx
# MINIMAX_CN_BASE_URL=             ← 注释掉，走内置默认
MINIMAX_API_KEY=YOUR_API_KEY-xxx...xxx
```

### 内置provider vs custom_providers 区别

| 特性 | `providers` (内置) | `custom_providers` |
|---|---|---|
| 定义位置 | `plugins/model_providers/` | config.yaml |
| base_url | 内置默认，可被 .env 覆写 | 显式配置 |
| api_mode | 内置定义（如 anthropic_messages） | 自动检测或显式 |
| 环境变量 | `api_key_env_var` (在 provider 定义里) | `key_env` |
| 适用场景 | MiniMax、DeepSeek、GLM 等官方 | 任意兼容OpenAI API的中转 |
