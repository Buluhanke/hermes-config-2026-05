# Gemma 4 E4B 与 MobileExplorer — M4 24GB 视觉模型评估

摘自 `idle_learning/references/idle-learning-2026-06-01-r4-gemma4-e4b-mobile-explorer.md`

## Gemma 4 E4B 对 screen_watcher 的价值

| 能力 | qwen3-vl:2b | gemma4:e4b | 提升 |
|------|-------------|------------|------|
| 场景分类 | 3s ✅ | 更快预期 | 持平或略快 |
| 内容分析 | ~5s | 57 tok/s | 更快 |
| inline OCR | ❌ 无 | ✅ 日文/英文 OCR | **新增能力** |
| ASR | ❌ | ✅ 3语言完美转写 | 新增模态 |
| 内存 | 1.76 GB | ~5.5 GB | 总 7.3GB 仍充分 |

## MobileExplorer 并行探索思路

screen_watcher handler 的 20-30s 全周期（场景分类 3s + 内容分析 ~5s + 冷却）可被利用：
- 场景分类完成后，启动轻量 subprocess 做 UI 元素探测
- 探测结果注入下次分析的 context
- 不阻塞主 handler 流程

详见: `idle_learning/references/idle-learning-2026-06-01-r4-gemma4-e4b-mobile-explorer.md`
