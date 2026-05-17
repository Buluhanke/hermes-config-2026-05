# Model Picker 沟通指南（2026-05-17）

## 用户问"/model 选择器里哪个是哪个"时

**直接回答前缀区分**：
- `deepseek/xxx` = 直连付费（`api.deepseek.com`）
- `nous/xxx` = 网页授权免费/套餐（Nous Portal）
- `openrouter/xxx` = OpenRouter 中转

**不要做**：解释架构、说"Provider 选择器第一层第二层"、分析技术细节。

## Model Picker UX 行为

`hermes model` 是两层选择器：

### 第一层：Provider 选择
```
╭─ ⚙ Model Picker — Select Provider ─────╮
│ Current: deepseek/deepseek-v4-flash on Nous Portal
│ ❯ Nous Portal (24 models)  ← current
│   DeepSeek (4 models)
│   ...
```

### 第二层：模型选择
以 Nous Portal 为例，**上方是收费模型**（标价），**底部是免费模型**（free）：

```
╭─ ⚙ Model Picker — Nous Portal ────────╮
│   ...（24 个带价格的模型）
│   deepseek/deepseek-v4-pro       $0.43  $0.87  $0.00
│   ← Back
│ ❯ Cancel
```

往下翻到底：
```
Available free models:
->   deepseek/deepseek-v4-flash  free  free  free
     stepfun/step-3.5-flash      free  free  free
```

## 常见问答模板

**Q**: "这里面哪里是我的免费模型？"
**A**: 「往下翻到底，`Available free models` 区域里 `deepseek/deepseek-v4-flash` 就是免费的。」

**Q**: "deepseek-v4-flash 和 deepseek-v4-pro 有什么区别？"
**A**: 「flash = 免费（Nous Portal 上），pro = 收费 $0.43/$0.87。」

**Q**: "选哪个才是免费的？"
**A**: 「Nous Portal → 翻到底 → `deepseek/deepseek-v4-flash  free`。」
