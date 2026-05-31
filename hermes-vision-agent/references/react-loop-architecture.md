# ReAct循环架构说明

## Playwright + LLM = VLM的替代方案

### 实测性能对比（M4 Mac mini）

| 方案 | 耗时 | 依赖 |
|------|------|------|
| browser_snapshot (DOM) | 8ms | hermes工具 |
| LLM理解+决策 (DeepSeek) | 0.8s | DeepSeek API |
| Playwright 执行 (click/fill) | 0.3s | Playwright |
| **总计** | **~1.2s/步** | 无本地模型 |

VLM方案：截屏(87ms) → qwen3-vl:2b 分析(2-4s) → 执行 → 总3-5s/步

**DOM+LLM比VLM快3-4倍，且不消耗本地GPU内存。**

## LLM决策指令格式

脚本期望LLM返回的格式：
```
type input[name="custname"] Hermes
type input[name="custemail"] hermes@test.com
click button
done
```

每行一个操作，最后一行可以是 `done` 或 `fail[原因]`。

## API优先级

1. DeepSeek（最快，0.8s）→ 稳定优先
2. MiniMax/AICODEE → 主模型但有时429
3. AICodee备用 → token中转

## 错误处理

LLM常犯的错误：
- 一次输出多行，但格式不规范（前面带 `-` 号）
- 对空DOM（动态加载页）反复输出同样的指令
- 超时后输出空字符

修复：脚本内对 `-` 做 strip，对重复输出做去重（max_steps=3），超时用 timeout 兜底。
