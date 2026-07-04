# MiniMax-M3 自定义代理服务 Provider 修复指南

## 问题场景 (2026-07-04)

用户报错：`⚠️ Provider authentication failed. Unknown provider 'custom:123.56.67.77:9100'`

用户说明：`"错了，是走第三方代理的，base url：http://123.56.67.77:9100"`

## 根因分析

配置文件中 provider 字段格式错误：
```yaml
# ❌ 错误格式
provider: custom:123.56.67.77:9100

# ✅ 正确格式
provider: openrouter  # 使用 OpenRouter 兼容格式
```

## 修复步骤

### 1. 检查当前配置
```bash
grep -A 3 -B 3 "MiniMax-M3" ~/.hermes/config.yaml
```

### 2. 修改 provider 字段
```bash
sed -i '' 's/provider: custom:123.56.67.77:9100/provider: openrouter/' ~/.hermes/config.yaml
```

### 3. 更新 fallback_chain
```bash
hermes config set fallback_chain openrouter
```

### 4. 重启 gateway
```bash
hermes gateway restart
```

## 配置文件正确格式

```yaml
fallback_providers:
  - api_key: MINIMAX_API_KEY
    base_url: http://123.56.67.77:9100
    label: MiniMax M3 (代理服务)
    model: MiniMax-M3
    provider: openrouter  # 关键修复点
    request_timeout_seconds: 30
```

## 关键要点

1. **第三方代理服务** 应使用 `provider: openrouter`，而非 `custom:xxx` 格式
2. **OpenAI 兼容端点** 的 provider 字段必须符合 Hermes 规范
3. **重启 gateway** 是必须的，配置不会热加载
4. **保持 API key 配置**，可以直接写在 config.yaml 中

## 验证修复

修复后检查：
```bash
grep -A 3 -B 3 "MiniMax-M3" ~/.hermes/config.yaml
hermes config show | grep fallback_chain
```

## 相关技能

- `hermes-provider-fallback-tuning` - 提供完整的 provider 调优指南
- `hermes-runtime-fortress` - Hermes 运行时守护技能