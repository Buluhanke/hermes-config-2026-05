#!/bin/bash

# MiniMax-M3 Provider Audit Script
# 检查第三方代理服务的 provider 配置是否正确

echo "🔍 MiniMax-M3 Provider 配置审计"
echo "================================="

# 检查配置文件中的 MiniMax-M3 配置
echo "1. 检查 MiniMax-M3 配置..."
if grep -q "MiniMax-M3" ~/.hermes/config.yaml; then
    echo "✅ MiniMax-M3 配置存在"
    echo ""
    echo "当前配置："
    grep -A 5 -B 2 "MiniMax-M3" ~/.hermes/config.yaml
    echo ""
    
    # 检查 provider 字段
    PROVIDER_LINE=$(grep -A 3 "MiniMax-M3" ~/.hermes/config.yaml | grep "provider:")
    if [[ $PROVIDER_LINE == *"custom:"* ]]; then
        echo "❌ 问题: provider 字段使用 'custom:' 格式"
        echo "   修复: sed -i 's/provider: custom:123.56.67.77:9100/provider: openrouter/' ~/.hermes/config.yaml"
    elif [[ $PROVIDER_LINE == *"openrouter"* ]]; then
        echo "✅ 正确: provider 字段使用 'openrouter' 格式"
    else
        echo "⚠️  未知: provider 字段格式 - $PROVIDER_LINE"
    fi
else
    echo "❌ MiniMax-M3 配置不存在"
fi

echo ""
echo "2. 检查 fallback_chain 配置..."
if grep -q "fallback_chain" ~/.hermes/config.yaml; then
    FALLBACK_CHAIN=$(grep "fallback_chain" ~/.hermes/config.yaml)
    echo "当前 fallback_chain: $FALLBACK_CHAIN"
    
    if [[ $FALLBACK_CHAIN == *"openrouter"* ]]; then
        echo "✅ fallback_chain 包含 openrouter"
    else
        echo "⚠️  fallback_chain 不包含 openrouter"
    fi
else
    echo "❌ fallback_chain 配置不存在"
fi

echo ""
echo "3. 检查 API Key 配置..."
if grep -q "MINIMAX_API_KEY" ~/.hermes/config.yaml; then
    echo "✅ MINIMAX_API_KEY 在配置文件中设置"
else
    echo "❌ MINIMAX_API_KEY 未在配置文件中设置"
    echo "   检查 ~/.hermes/.env 文件中是否有 MINIMAX_API_KEY"
fi

echo ""
echo "4. 检查 Gateway 状态..."
if pgrep -f "hermes.*gateway" > /dev/null; then
    echo "✅ Gateway 正在运行"
    GATEWAY_PID=$(pgrep -f "hermes.*gateway" | grep -v grep)
    echo "   PID: $GATEWAY_PID"
else
    echo "❌ Gateway 未运行"
fi

echo ""
echo "📋 总结:"
echo "- 如果显示 ❌ 问题，请运行修复命令"
echo "- 修复后需要重启: hermes gateway restart"
echo "- 重启后验证: hermes -p \"test\""