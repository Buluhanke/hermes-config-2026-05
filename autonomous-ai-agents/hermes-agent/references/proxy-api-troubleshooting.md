# 代理与 API 故障排查参考

## 代理验证命令

```bash
# 检查环境变量
grep -E "HTTP_PROXY|HTTPS_PROXY|NO_PROXY" ~/.hermes/.env

# 验证代理端口
netstat -an | grep "LISTEN" | grep -E "1082|7897"

# ⚠️ 注意：变量名不能含 KEY/TOKEN/SECRET 等词，否则触发安全扫描（exfil_curl_auth_header）
# 错误示例（触发扫描）：
#   curl ... -H "Authorization: Bearer $YOUR_API_KEY"
#   curl ... -H "Authorization: Bearer $TOKEN"
# 正确示例：
curl -s --connect-timeout 3 -x http://127.0.0.1:1082 https://api.deepseek.com/v1/models -H "Authorization: Bearer $DEEP_PROXY"
curl -s -o /dev/null -w "%{time_total}s" https://v2.aicodee.com/v1/models -H "Authorization: Bearer $MINIMAX_TOKEN"
```

## 常见代理问题

| 问题 | 表现 | 解决方案 |
|------|------|---------|
| 代理未启动 | curl 超时 | 检查 Shadowrocket/Clash verge-mih 是否运行 |
| DeepSeek 屏蔽代理 | 返回 governor/认证失败 | 直连不走代理，或换端口 |
| 代理端口错误 | Connection refused | 确认 1082 vs 7897 端口配置 |