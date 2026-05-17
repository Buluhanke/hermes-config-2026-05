# MiniMax Provider 真相清单

## 两个 MiniMax provider 的本质区别

| Provider | 真实 endpoint | 可用模型 | 状态 |
|----------|--------------|---------|------|
| `minimax` (minimax.io) | https://api.minimax.io/v1 | 列表有 M2.7 | **假的**，无真实渠道 |
| `minimax-cn` (minimaxi.com) | https://api.minimaxi.com/v1 | M2.7, M2.5, M2.1 | **真的**，官方渠道 |

## V2.aicodee.com 中转

- 列表有 `MiniMax-M2.7-highspeed`
- 实际调用返回 503 `model_not_found` = distributor 上没有可用渠道
- **中转已死，但配置里依然填主模型位置**，等它恢复
- Fallback 触发条件：503 + `model_not_found` 不在标准 fallback 条件里，需要代码修复

## 当前模型链（config.yaml）

```yaml
model:
  default: V2.aicodee.com/MiniMax-M2.7-highspeed  # 主（已死，等恢复）
  provider: custom
  fallback_model:
  - provider: minimax-cn      # Fallback 1：minimaxi.com 官方渠道 ✅
    model: MiniMax-M2.7
  - provider: deepseek        # Fallback 2
    model: deepseek-v4-flash
  base_url: https://v2.aicodee.com/v1
```

## 手动切换命令

切到 minimax-cn（minimaxi.com）直接用：
```bash
sed -i '' 's/default: V2.aicodee.com\/MiniMax-M2.7-highspeed/default: minimax-cn\/MiniMax-M2.7/' ~/.hermes/config.yaml
```

恢复 V2.aicodee.com 主模型：
```bash
sed -i '' 's/default: minimax-cn\/MiniMax-M2.7/default: V2.aicodee.com\/MiniMax-M2.7-highspeed/' ~/.hermes/config.yaml
```

## 问题：model_not_found 不触发 fallback

V2.aicodee.com 返回的 503 `model_not_found`（错误码在 response body 里）不在标准 fallback 触发条件中。需要修复 fallback 代码对这个错误的处理。

## 验证方法

```bash
hermes status 2>/dev/null | grep -E "Model|Provider"
```