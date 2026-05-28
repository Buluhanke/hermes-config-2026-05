# Config 巡检清单（主动触发）

## 每次配置类任务前必查

### 1. fallback_model 是否启用（最高优先级）

```bash
grep -A3 "fallback_model:" ~/.hermes/config.yaml
```

**判断标准**：
- `fallback_model:` 下有 `provider:` 和 `model:` = ✅ 已启用
- `fallback_model:` 下面是注释 `#` = ❌ 未启用，高危

**风险**：未启用时，主模型故障 → 所有渠道（QQ/微信/Telegram）全部卡死，无自动切换。

**当前推荐 fallback**：`deepseek/deepseek-v4-flash`

**启用命令**（当被注释时）：
```bash
sed -i '' 's/# fallback_model:/fallback_model:/; s/#   provider: openrouter/  provider: deepseek/; s/#   model: anthropic\/claude-sonnet-4/  model: deepseek-v4-flash/' ~/.hermes/config.yaml
```

### 2. 主模型配置

```bash
grep -A6 "^model:" ~/.hermes/config.yaml | head -10
```

确认 `default` 是否为当前真实在用的模型。参考 `references/aicodee-provider-setup.md` 确认当前主链路状态。

### 3. API Key 有效性

```bash
hermes status 2>/dev/null | grep -E "API Keys|MiniMax|DeepSeek|OpenRouter"
```

确认关键 provider 的 key 状态为 ✓。

---

**触发时机**：用户要求"检查模型配置"、"检查路由"、或任何配置类任务。主动巡检，不需要用户提醒。
