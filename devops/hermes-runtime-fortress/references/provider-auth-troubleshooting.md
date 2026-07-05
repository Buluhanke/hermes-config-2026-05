# Provider认证故障排查指南 (2026-07-05)

## 故障模式

### 模式1: HTTP 401 认证失败
**现象**: Gateway日志显示 `HTTP 401: Missing Authentication header`
**根因**: Provider配置的API key未设置或过期
**排查步骤**:
```bash
# 1. 查看Gateway日志
tail -20 ~/.hermes/logs/gateway.log | grep -i "401\|authentication"

# 2. 检查配置文件
grep -A 10 -B 5 "provider" ~/.hermes/config.yaml

# 3. 测试API连接
curl -s -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  "https://api.example.com/v1/chat/completions" \
  -d '{"model":"model-name","messages":[{"role":"user","content":"test"}]}'
```

### 模式2: Provider切换失败
**现象**: Fallback chain频繁切换，响应延迟
**根因**: 主Provider认证失败，频繁回退到备用Provider
**排查步骤**:
```bash
# 1. 检查当前Provider
hermes config show

# 2. 验证所有Provider的API key
echo "ZAI_KEY: ${ZAI_API_KEY:0:10}..."
echo "GLM_KEY: ${GLM_API_KEY:0:10}..."
echo "NVIDIA_KEY: ${NVIDIA_API_KEY:0:10}..."

# 3. 逐个测试Provider连接
curl -s -H "Authorization: Bearer ${GLM_API_KEY}" \
  "https://open.bigmodel.cn/api/paas/v4/models" | jq '.data'
```

## 修复方案

### 立即修复流程
```bash
# 1. 定位可用的Provider
for provider in zai glm nvidia openrouter gemini cerebras agnes; do
  if [ -n "${${provider}_API_KEY}" ]; then
    echo "Testing $provider..."
    curl -s -H "Authorization: Bearer ${${provider}_API_KEY}" \
      "https://api.example.com/v1/models" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
      echo "✓ $provider 可用"
      break
    fi
  fi
done

# 2. 切换到可用Provider
hermes config set model.provider <available_provider>
hermes config set model.default <model_name>

# 3. 重启Gateway
/Users/aimac/.hermes/scripts/restart_gateway.sh
```

### Provider优先级建议
1. **GLM** (智谱): 稳定，中文支持好
2. **ZAI** (Z.AI): 响应快，但key易过期
3. **NVIDIA** (OpenRouter): 大模型，但需要GPU
4. **Gemini** (Google): 免费额度，稳定
5. **Cerebras** (OpenRouter): 免费极速
6. **Agnes** (Apihub): 最终兜底

### 环境变量检查清单
```bash
# 必须设置的环境变量
export GLM_API_KEY="your_glm_key"
export ZAI_API_KEY="your_zai_key"
export NVIDIA_API_KEY="your_nvidia_key"
export GEMINI_API_KEY="your_gemini_key"
export CEREBRAS_API_KEY="your_cerebras_key"
export AGNES_API_KEY="your_agnes_key"
```

## 预防措施

### 1. 定期检查
```bash
# 每周自动检查所有Provider
hermes cron create \
  --name "provider-health-check" \
  --schedule "0 3 * * 0" \
  --prompt "bash ~/.hermes/scripts/provider_health_check.sh" \
  --deliver local
```

### 2. 自动切换机制
```bash
# 创建Provider健康检查脚本
cat > ~/.hermes/scripts/provider_health_check.sh << 'EOF'
#!/bin/bash
providers=("glm" "zai" "nvidia" "gemini" "cerebras" "agnes")
for provider in "${providers[@]}"; do
  api_key_var="${provider^^}_API_KEY"
  if [ -n "${!api_key_var}" ]; then
    curl -s -H "Authorization: Bearer ${!api_key_var}" \
      "https://api.example.com/v1/models" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo "⚠️ $provider API 失效" >> ~/.hermes/logs/provider_health.log
    fi
  fi
done
EOF
chmod +x ~/.hermes/scripts/provider_health_check.sh
```

## 故障案例

### 案例1: ZAI key过期 (2026-07-05)
**问题**: Provider authentication failed，fallback到GLM
**解决**: 切换到GLM provider
```bash
hermes config set model.provider glm
hermes config set model.default glm-4-flash
```

### 案例2: 环境变量未设置
**问题**: API key显示为"not set"
**解决**: 设置环境变量到 ~/.hermes/.env
```bash
echo "GLM_API_KEY=your_key_here" >> ~/.hermes/.env
source ~/.hermes/.env
```

## 联系支持
如果问题持续存在，请检查：
1. API key是否正确
2. 网络连接是否正常
3. Provider服务是否维护
4. 配置文件语法是否正确