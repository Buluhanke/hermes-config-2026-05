# NV qwen3.5-397b DEGRADED 参考（2026-07-04）

## 症状
- qwen/qwen3.5-397b-a17b 在 NVIDIA NIM (`https://integrate.api.nvidia.com/v1`) 超时 70s+ 无响应
- 同 key 其他模型（Nemotron/Llama/Gemma）正常返回
- 有时返回 `400 Bad Request: DEGRADED function cannot be invoked`

## 根因
NVIDIA 官方确认该模型后端节点处于 DEGRADED 状态，非配置/网络问题。

## 官方论坛报告
- 2026-03-09: All requests time out — https://forums.developer.nvidia.com/t/qwen3-5-397b-a17b-all-requests-time-out/362928
- 2026-05-31: Bug Report — DEGRADED error — https://forums.developer.nvidia.com/t/bug-report-qwen-qwen3-5-397b-a17b-endpoint-returning-degraded-error/371828

## 历史延迟基线
| 日期 | 延迟 | 状态 |
|------|------|------|
| 2026-06-28 | 112-144s | 正常 |
| 2026-06-29 | 24-72s | 正常 |
| 2026-06-30 | 9.6s | 正常 |
| 2026-07-03 10:44 | 36s | 最后成功 |
| 2026-07-04 | 超时 70s+ | DEGRADED |

## 修复操作（已执行）
1. `sed -i '' '21s/request_timeout_seconds: 20/request_timeout_seconds: 120/' ~/.hermes/config.yaml`
2. 验证: `python3 -c "import yaml; yaml.safe_load(open('config.yaml')); print('YAML OK')"`
3. gateway 重启（需从外部杀进程）

## 恢复后验证
```bash
unset https_proxy http_proxy && curl -s --connect-timeout 20 -X POST \
  "https://integrate.api.nvidia.com/v1/chat/completions" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3.5-397b-a17b","messages":[{"role":"user","content":"ok"}],"max_tokens":5}'
```

## 禁止事项
- ❌ 禁止用 Python yaml.dump() 写 config.yaml — 会破坏 providers dict→list 结构
- ❌ 禁止 source .env 找 key — .env 里有 Chrome.app 路径会触发命令未找到
- ✅ 用 `grep "^NVIDIA_API_KEY=" ~/.hermes/.env | cut -d= -f2` 取 key
- ✅ 用 `sed -i '' '行号s/旧值/新值/'` 改配置单行
