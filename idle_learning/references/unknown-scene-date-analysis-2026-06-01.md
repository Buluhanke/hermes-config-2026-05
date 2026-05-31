# Unknown Scene Rate — 按日期分片分析（2026-06-01）

## 核心结论

全量 unknown 率（42-49%）= **历史污染数据**。按日期分片后，当前 qwen3-vl:2b handler 的 unknown 率为 **0%**。

## 数据证据

### May 31 全天
```
场景类型分布（280 条）：
  unknown: 280 (96%)
  other:   11 (4%)
```
- smolvlm2-agentic-gui 已从 Ollama registry 下线 → handler HTTP 请求失败 → 全部返回 "unknown"
- 这是服务可用性故障，不是模型质量问题

### June 1 00:06 之后
```
场景类型分布（~80 条）：
  other:   79 (99%)
  browser:  1 (1%)
  unknown:  0 (0%)
```
- handler 更新至 qwen3-vl:2b 版本（bak timestamp 00:24，当前版本 01:38）
- 场景分类正常工作：空闲桌面 → "other"，浏览器 → "browser"
- 否定词检测生效：所有 "没有需要处理的内容或异常" → [silent]

## 诊断命令

```bash
# 按日期分片统计
awk '/2026-06-01 00:06/ {found=1} found' ~/.hermes/logs/screen_trigger.log | grep "场景类型:" | sort | uniq -c | sort -rn

# 查看最新 N 条 unknown 记录
grep "场景类型: unknown" ~/.hermes/logs/screen_trigger.log | tail -10

# 全量场景分布（含历史）
grep "场景类型:" ~/.hermes/logs/screen_trigger.log | sed 's/.*场景类型: //' | sed 's/\s*$//' | sort | uniq -c | sort -rn
```

## 产线日志污染现象

smolvlm2 时代（~May 30-31）的 scene classification 输出中包含结构化 JSON action tokens：
- `click(x=0.974, y=0.0...)`
- `type('success')`  
- `answer('1688')`
- `final_answer('The image...')`

这些被 smolvlm2 训练数据中的 action 模板污染，不是合法的场景分类。切换到 qwen3-vl:2b（通用 VLM）后已消除。

## 对 DRY_RUN=False 过渡的影响

| 条件 | 全量统计 | 日期分片后 |
|------|---------|-----------|
| ① 基线数据 ≥ 500 | ✅ 730+ | ✅ |
| ② unknown < 30% | ❌ 42% | ✅ 0% (June 1) |
| ③ 3+ scenes > 50 | ❌ | 待重新评估 |

**结论**：条件②实际已达标。下一步可推进条件③-⑥评估，无需等 Ollama Watchdog。
