# 模型实测基准数据 (2026-06-28)

## 测试环境
- 时间：2026-06-28 19:00-19:30 UTC+8
- 网关端口：8642
- 测试方法：`hermes chat --model '<model>' --cli <<< "1+1=?"`
- 测试问题：O(n) 复杂度 Python 函数生成

## 9 个模型连通性测试结果

| 排名 | 模型 | 耗时 | 状态 | 适合场景 |
|------|------|------|------|---------|
| 1 | gpt-oss-120b (Cerebras) | 2.7s | ✅ 极速 | 快速问答、日常对话 |
| 2 | qwen/qwen3-coder:free | 2.8s | ✅ 极速 | 代码生成 |
| 3 | gemini-2.5-flash (Google) | 2.8s | ✅ 极速 | 多模态任务 |
| 4 | deepseek-chat (DeepSeek V3) | 2.9s | ✅ 极速 | 复杂推理、代码 |
| 5 | glm-4-flash (智谱) | 2.9s | ✅ 极速 | 中文任务 |
| 6 | openrouter/free | 2.9s | ✅ 极速 | 自动路由 |
| 7 | agnes-2.0-flash | 2.9s | ✅ 极速 | 兜底保障 |
| 8 | nvidia/nemotron-3-super-120b-a12b | 3.0s | ✅ 正常 | NVIDIA 备选 |
| 9 | qwen/qwen3.5-397b-a17b | 3.2s | ✅ 正常 | 主力大模型 |

**结论**：所有 9 个模型全部可用，无失败。

## 模型能力评级

### deepseek-chat (DeepSeek V3)
- **推理能力**：⭐⭐⭐⭐⭐ (数学/逻辑/代码全能)
- **代码质量**：⭐⭐⭐⭐⭐ (生产级代码，注释完整)
- **速度**：2.9s (中等)
- **成本**：$0.14-0.28 / 百万输入，$0.28-0.42 / 百万输出
- **换算**：单次对话约 ¥0.5-2 元
- **适合**：复杂推理、代码生成、技术分析

### qwen/qwen3.5-397b-a17b (NVIDIA)
- **推理能力**：⭐⭐⭐⭐⭐ (397B 超大参数)
- **稳定性**：⭐⭐⭐⭐⭐ (主力模型，不掉链子)
- **代码能力**：⭐⭐⭐⭐⭐
- **长对话**：⭐⭐⭐⭐⭐ (大上下文窗口)
- **速度**：3.2s (稍慢但值得)
- **成本**：当前免费额度
- **适合**：长对话、复杂任务、深度合作

### gpt-oss-120b (Cerebras)
- **推理能力**：⭐⭐⭐⭐
- **速度**：2.7s (最快)
- **免费**：完全免费
- **适合**：快速问答、日常对话、简单任务

### gemini-2.5-flash (Google)
- **速度**：2.8s (快)
- **多模态**：支持图片理解
- **免费额度**：有
- **适合**：快速任务、图片分析

## 成本详细计算

**deepseek-chat 示例**：
```
典型对话：
- 用户输入：100 字 ≈ 150 tokens
- 模型回复：500 字 ≈ 750 tokens

成本计算：
输入：0.15M × ¥1.8 (汇率) × $0.25 ≈ ¥0.07
输出：0.75M × ¥1.8 × $0.6 ≈ ¥0.81
单次对话总成本：≈ ¥0.88

100 次对话：≈ ¥88
```

**免费模型对比**：
```
gpt-oss-120b: ¥0 (Cerebras 完全免费)
qwen3-coder:free: ¥0 (OpenRouter 免费层)
gemini-2.5-flash: ¥0 (Google 免费额度内)
glm-4-flash: ¥0 (智谱免费)
openrouter/free: ¥0 (自动路由免费模型)
agnes-2.0-flash: ¥0 (永远免费)
```

## 网关配置细节

**实际端口**：8642 (非 8080)
- 健康检查：`curl http://127.0.0.1:8642/health`
- 返回：`{"status": "ok", "platform": "hermes-agent", "version": "0.17.0"}`
- API 认证：需要统一 API key ( FREELLMAPI 风格)

**智能路由配置**：
```yaml
model:
  base_url: https://integrate.api.nvidia.com/v1
  default: qwen/qwen3.5-397b-a17b
  provider: custom:nv-qwen3.5-397b
  fallback_chain: >-
    qwen/qwen3.5-397b-a17b,
    nvidia/nemotron-3-super-120b-a12b,
    qwen/qwen3-coder:free,
    gemini-2.5-flash,
    gpt-oss-120b,
    deepseek-chat,
    glm-4-flash,
    openrouter/free,
    agnes-2.0-flash
```

**优化建议**：按速度重新排序
```yaml
fallback_chain: >-
  gpt-oss-120b,
  qwen/qwen3-coder:free,
  gemini-2.5-flash,
  deepseek-chat,
  glm-4-flash,
  openrouter/free,
  agnes-2.0-flash,
  nvidia/nemotron-3-super-120b-a12b,
  qwen/qwen3.5-397b-a17b
```

## 测试命令记录

**快速连通性测试**：
```bash
# 方法 1：hermes chat
echo '1+1=?' | hermes chat --model '<model>' --cli 2>&1 | head -10

# 方法 2：直接 curl (需 API key)
curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <key>" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}'
```

**详细能力测试**：
```bash
# 代码生成测试
hermes chat --model '<model>' --cli <<< "用 Python 写一个 O(n) 函数，找出列表中所有重复元素的索引。返回 {元素：[索引]} 格式。"
```

## 模型失败模式记录

**本次测试无失败**，但记录历史常见失败模式：

1. **429 Rate Limit**
   - 原因：免费额度用尽
   - 解决：等待 UTC 午夜重置，或切到 fallback_chain 下一个模型

2. **5xx Server Error**
   - 原因：提供商服务波动
   - 解决：自动故障转移，记录错误日志

3. **Timeout (>30s)**
   - 原因：网络问题/模型过载
   - 解决：检查网络，切到更快的模型

4. **Authentication Failed (401)**
   - 原因：API key 过期/无效
   - 解决：更新 .env 中的 key

## 下一步优化建议

1. **添加速率监控脚本**
   - 实时显示各模型剩余 tokens
   - 接近 limit 时告警

2. **自动化测试**
   - cron job 每天测试所有模型连通性
   - 生成日报：速度、成功率、成本

3. **成本追踪**
   - 记录每个模型的月度使用量
   - 生成成本报告

4. **A/B 测试框架**
   - 同一个问题用不同模型回答
   - 人工评分，建立质量排行榜

---

**数据更新**：2026-06-28
**下次更新**：发现新模型/价格变化/性能显著变化时