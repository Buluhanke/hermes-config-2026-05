# MiniMax 配置清理 SOP — 模型切换实战 (2026-07-04)

> 关联 SKILL: `meta/proactive-execution/SKILL.md` v1.19.0
> 触发用户原话: "MiniMax - 未登录清除目录"

## 实战背景

用户要求清除 MiniMax 配置并切换到正常工作的模型。经过多次尝试 API key 配置失败后，直接切换到稳定可用的 Z.AI 模型。

## 问题识别

**初始状态**:
- 默认模型: MiniMax-M3 (custom:123.56.67.77:9100)
- 认证状态: ✗ MiniMax (invalid API key)
- 可用模型: 5 个正常工作

**根因分析**:
- MiniMax 代理端点认证失败
- API key 配置多次尝试无效
- 需要立即切换到稳定模型

## 清理切换 SOP

### 1. 状态检查
```bash
# 检查当前配置
hermes config show | grep "Model"
# 期望: {'default': 'MiniMax-M3', 'provider': 'custom:123.56.67.77:9100', 'base_url': 'https://integrate.api.nvidia.com/v1'}

# 检查认证状态
hermes doctor | grep "MiniMax"
# 期望: ✗ MiniMax (invalid API key)
```

### 2. 配置切换
```bash
# 切换到稳定提供商
hermes config set provider zai

# 修复模型提供商
sed -i '' 's/custom:123.56.67.77:9100/zai/' ~/.hermes/config.yaml

# 修复 API 端点
sed -i '' 's|https://integrate.api.nvidia.com/v1|https://openrouter.ai/api/v1|' ~/.hermes/config.yaml
```

### 3. 自动修复配置
```bash
# 修复过期键值
hermes doctor --fix
```

### 4. 验证状态
```bash
# 检查模型配置
hermes config show | grep "Model"
# 期望: {'default': 'glm-4.5-flash', 'provider': 'zai', 'base_url': 'https://openrouter.ai/api/v1'}

# 检查 API 连接
hermes doctor | grep "API Connectivity"
# 期望: ✓ OpenRouter API, ✓ Z.AI / GLM, ✓ DeepSeek, ✓ NVIDIA NIM, ✓ gemini
```

## 可用模型清单

**✅ 正常工作的模型**:
- OpenRouter API
- Z.AI / GLM (当前使用)
- DeepSeek
- NVIDIA NIM
- gemini

**❌ 不工作的模型**:
- MiniMax 代理 (123.56.67.77:9100) - 认证失败
- GitHub Copilot - 未配置
- Ollama Cloud - 未检查
- Google - 未检查
- MiniMax 官网 - 未检查

## 关键教训

1. **立即切换原则**: 用户明确要求清除时，立即切换到稳定可用模型，不反复尝试无效配置
2. **配置验证**: 每次修改后立即用 `hermes doctor` 验证状态
3. **自动修复**: 利用 `hermes doctor --fix` 自动处理配置格式问题
4. **模型可用性**: 优先使用经过验证的稳定模型，避免在认证失败的模型上浪费时间

## 触发词

- "MiniMax - 未登录清除目录" / "清除 MiniMax" / "切换模型" / "MiniMax 认证失败"
- "哪些模型正常用" / "哪些模型可用" / "模型切换"

## 关联技能

- `hermes-provider-fallback-tuning` — 模型路由配置管理
- `hermes-runtime-fortress` — 网关配置健康检查