# MoA (Mixture of Agents) 配置参考 — 2026-07

源自官方文档：https://hermes-agent.nousresearch.com/docs/user-guide/features/mixture-of-agents

## 架构变化（v0.17）

MoA 不再是 toolset（`hermes tools list` 不会显示 `moa`）。
MoA 是**虚拟 provider** — preset 名称出现在所有模型选择器里。

## 新配置格式（presets）

```yaml
moa:
  default_preset: default
  presets:
    default:
      reference_models:
        - provider: openrouter
          model: anthropic/claude-sonnet-4
        - provider: openrouter
          model: openai/gpt-5.5
      aggregator:
        provider: openrouter
        model: anthropic/claude-opus-4.8
      reference_max_tokens: 600    # 可选：限制 advisor 输出
      reference_temperature: 0.7   # 可选
      aggregator_temperature: 0.4  # 可选
      max_tokens: 4096
      enabled: true
```

## MoA 的工作原理（agent loop 内）

每轮：
1. 并行调用所有 reference_models（无 tool schema — 便宜）
2. 将参考输出追加到 aggregator 的对话上下文中
3. aggregator 获得正常 tool schema → 正常输出 tool calls
4. 如果 aggregator 调了工具 → Hermes 正常执行
5. 下一轮迭代再次走 MoA 流程

## 使用方式

| 方式 | 命令 |
|---|---|
| 临时 MoA 调用 | `/moa 你的提示词`（跑完自动恢复原模型） |
| 全局切到 MoA | `/model default --provider moa` |
| 终端管理 | `hermes moa list` / `hermes moa configure [name]` |

## 关键特性

- **Prompt caching 不受影响**：参考模型收到固定的 trimmed 输入；aggregator 的新上下文在末尾追加，不影响已缓存的 prefix
- **credential 失败不 abort**：单个 reference model 失败仍继续用其他
- **aggregator 不能递归**：不能指向另一个 MoA preset
- **benchmark 数据**：opus-4.8 + gpt-5.5 reference 在 HermesBench 得 0.8202（高于 opus 独自 0.7607 和 gpt-5.5 独自 0.7412）

## `hermes moa` CLI 子命令

```bash
hermes moa list                    # 列出所有 preset
hermes moa configure               # 编辑默认 preset
hermes moa configure review        # 创建/更新命名 preset
hermes moa delete review           # 删除命名 preset
```

## 旧格式 vs 新格式对照

| 旧字段 | 新字段 | 说明 |
|---|---|---|
| `moa.models[]` | `moa.presets.<name>.reference_models[]` | 参考模型列表 |
| `moa.aggregator` | `moa.presets.<name>.aggregator` | 聚合器 |
| — | `moa.default_preset` | 默认 preset 名称 |
| — | `moa.presets.<name>.enabled` | 设为 false 时只走 aggregator（不 fan-out） |
| — | `moa.presets.<name>.reference_max_tokens` | 控制 advisor 输出长度（600 推荐） |

## 实战陷阱：provider 名来自自定义 fallback_providers 标签

**新格式需要 `provider:model` 完整对**，而旧格式直接用纯模型名字符串：

```yaml
# ❌ 旧格式
moa:
  models:
    - nv-qwen3.5-397b          # 纯模型名，assume 默认 provider
  aggregator: deepseek-chat    # 纯模型名
```

迁移时必须查出每个模型实际走哪个 provider。检查方法是看 `fallback_providers[]` 里的 `provider:` 字段：

```bash
grep -B 1 -A 6 'model: nv-qwen3.5-397b' ~/.hermes/config.yaml
# → 实际 provider 是 nv-qwen3.5-397b（自定义标签，走 OpenRouter 路由）
```

常见 provider 映射（从 fallback_providers 记录还原）：
- `deepseek-chat` → `provider: deepseek`（标准 DeepSeek API）
- `glm-4-flash` → `provider: glm`（智谱 API）
- `gemini-2.5-flash` → `provider: gemini`（Google API）
- `agnes-2.0-flash` → `provider: Apihub.agnes-ai.com`（自定义第三方）
- `nv-qwen3.5-397b` → `provider: nv-qwen3.5-397b`（自定义标签，OpenRouter 路由）

**写 presets 时不准用 model 名字符串** — 每条 `reference_models[]` 必须有 `provider:` + `model:` 两个字段，缺一不可。

## `hermes config set` 写 MoA 陷阱

`hermes config set` 写入新字段后**旧字段不会自动清除** — 旧 `moa.models[]` + `moa.aggregator` 残留且 Hermes 可能优先读旧字段：

```bash
# 写入新 presets 后，检查旧字段
grep -A 2 '^moa:' ~/.hermes/config.yaml
# 如果仍有 models: / aggregator: → 手动清掉
hermes config set moa.models '[]'
hermes config set moa.aggregator ''
# 再用 sed 删除空行
sed -i '' '/^  models: .*$/d' ~/.hermes/config.yaml
sed -i '' '/^  aggregator: .*$/d' ~/.hermes/config.yaml
```

## 迁移前备份

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.moa-bak.$(date +%Y%m%d)
```

随时对照检查：`grep -n 'models\|aggregator\|preset\|moa:' ~/.hermes/config.yaml`
