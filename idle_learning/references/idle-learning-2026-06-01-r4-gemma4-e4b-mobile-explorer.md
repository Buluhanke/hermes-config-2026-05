# Idle Learning 2026-06-01 (方向A) — Gemma 4 E4B 实测 + MobileExplorer

## 1. Gemma 4 E4B — M4 24GB 实测关键数据

**来源**: dev.to/akartit (2026-04-04, M4 Pro 24GB macOS Sequoia)
**ollama pull**: `gemma4:e4b` ✅ 直接可用

| 指标 | 值 |
|------|-----|
| 参数量 | Dense 4.5B |
| 模态 | Text + Image + Audio |
| Ollama 内存 | ~5.5 GB at 4-bit |
| Ollama 速度 | **57 tok/s** |
| MLX 速度 | 49 tok/s (内存少 40%) |
| 26B MoE on 24GB | ~2 tok/s (swap) — 不可用 |

### Image Understanding 实测

| 测试 | E4B | E2B |
|------|-----|-----|
| 泰国王宫识别 | Wat Phra Kaew (正确) | Grand Palace (泛化) |
| 日文 OCR | 新宿ラーメン通り ✅ | 同上 ✅ |
| 场景描述 | 详细+对比建筑风格 | 简短 |
| 速度 | 54 tok/s | 88 tok/s |

### Audio ASR 实测

| 语言 | E4B 耗时/质量 | E2B 耗时/质量 |
|------|-------------|--------------|
| 英语 | 1.0s / 完美+标点 | 2.8s / 乱码 |
| 法语 | 1.6s / 完美+重音 | 4.1s / 碎片 |
| 阿拉伯语 | 6.0s / 完美 | 6.0s / 乱码 |
| 法语→英语翻译 | 6.0s / 准确 | — |

### Coding 实测

- E4B: 生成 155 行 React + Tailwind 任务管理器（可用）
- E2B: 生成代码片段（不可用）

### 对 Hermes screen_watcher 的价值

- **inline OCR**: screen_watcher 的 "other" 场景包含中文/日文文本时，E4B 可同时做场景分类+OCR
- 5.5GB + qwen3-vl:2b 1.76GB = 7.3GB，24GB 充分
- 57 tok/s 足够实时
- Quick Start: `ollama run gemma4:e4b`

## 2. MobileExplorer: On-Device GUI Agent 推理加速

**arXiv**: 2605.26546 (2026-05-26, 6 days old)
**机构**: Runxi Huang, Liyu Zhang, Shengzhong Liu, Xiaomin Ouyang

### 核心创新

```
VLM 推理等待时间（长 per-step latency）
    ↓
利用空闲时间做轻量级并行 UI 元素探索
    ↓
探索轨迹记录为结构化 memory
    ↓
总结为上下文提示注入下一推理步骤
```

### 关键组件

1. **并行 UI 探测**: 在 VLM 推理期间，主动探测语义相关 UI 元素
2. **双层级回滚机制**: naive backtracking 失败时恢复初始 UI 状态
3. **探索轨迹摘要**: 结构化 memory → context hint → 注入 prompt

### Benchmark 结果

| 指标 | 改进 |
|------|------|
| 推理步数 | ↓ **23%** |
| 端到端延迟 | ↓ **23%** |
| 任务成功率 | ↑ **5%** 或持平 |

### 对 Hermes handler 的启发

当前 screen_watcher 场景分类 9-12s + 内容分析 ~12s = 20-30s 全周期。
这 20-30s 的 VLM 推理时间可被利用做：
- **并行 UI 元素探测**: 截取屏幕各区域，用轻量模板匹配检测变化
- **探索轨迹记录**: 检测到的 UI 变化记录为 memory
- **与 RoTS error recovery 结合**: 错误恢复期间并行探索

**落地可能性**: 高 — handler 是同步单线程，但可通过 subprocess 启动并行探测线程，用共享锁协调。不阻塞主 handler 流程。

## 3. 1-Bit Bonsai Image 4B

**来源**: prismml.com (5 days old, HN 108pts)
**类型**: 图像生成模型（非 VLM 理解）

| 指标 | 值 |
|------|-----|
| 参数量 | 4B (扩散 transformer) |
| 1-bit 大小 | ~1.21 GB |
| 变体 | 1-bit / ternary |
| 压缩比 | up to 8.3x |
| 运行方式 | llama.cpp (Metal 支持) |
| HuggingFace | prism-ml/Bonsai-4B-gguf |

**注意**: 这是图像生成模型，不是 GUI 视觉理解模型。但验证了 1-bit 技术已成熟可实用化。

## 4. InsiderLLM Mac 模型推荐 (Updated May 2026)

**来源**: insiderllm.com/guides/best-local-llms-mac-2026/

### 24GB Mac 层级

| 模型 | 大小 | 速度 | 推荐度 |
|------|------|------|--------|
| Qwen 3.6-27B Q4_K_M | ~16.8 GB | 18-28 tok/s | ⭐ 编码首选 (25.57 tok/s 实测) |
| Gemma 4 E4B | ~5.5 GB | 57 tok/s | ✅ 安全选择 |
| Qwen 3.5 9B Q8 | ~10 GB | 18-30 tok/s | ✅ 稳妥 |
| Qwen 3 14B Q4 | ~9 GB | 15-30 tok/s | ✅ 通用 |
| Qwen 3.6-35B-A3B | ~20 GB | ❌ 24GB 不够 | 需 32GB+ |

### 核心变化 (May 2026)

- Qwen 3.6-27B dense (April 22) 成为新旗舰编码模型, 77.2 SWE-bench, Apache 2.0
- Qwen 3.6-35B-A3B MoE (April 16) 仅 3B active/token, 性能接近 3B 模型
- Gemma 4 26B-A4B 作为替代 MoE 选项
- M5 Max 已发货但 Studio 延迟至 October 2026

## 5. 系统快照 (2026-06-01 01:50 UTC)

| 组件 | 状态 |
|------|------|
| screen_watcher | ✅ PID 8748, 持续运行 |
| 截图新鲜度 | ✅ current.png ~3.3MB (Jun 1 01:47) |
| Ollama runner | ✅ qwen3-vl:2b 活跃, 2.8GB RSS |
| 本地模型 | qwen2.5:1.5b (0.92GB), qwen3-vl:2b (1.76GB) |
| dry-run 总数 | 672 条 |
| 场景分布 | unknown 301(45%), browser 234(35%), other 88(13%), desktop 42(6%), wechat 6, calculator 3 |
| 否定词检测 | ✅ 持续生效 |
| Handler 响应 | scene ~3s, full cycle ~8s (比 6月1日前 35-47s 大幅优化) |
| 网络 | ✅ github:ok, hn:ok, firebase:ok |

### 场景分布变化趋势

| 日期 | dry-run | unknown | browser | other | desktop |
|------|---------|---------|---------|-------|---------|
| 05-31 06:00 | 468 | 184 (40%) | 233 (50%) | — | 42 (9%) |
| 06-01 01:41 | 668 | 301 (45%) | 234 (35%) | 77 (12%) | 42 (6%) |
| 06-01 01:50 | 672 | 301 (45%) | 234 (35%) | 88 (13%) | 42 (6%) |

"other" 增长 11 条 → 否定词检测正确工作，原 unknown 场景转为 other + [silent]

## 6. 下一步建议

1. 🟢 **尝试 pull gemma4:e4b** (~5.5GB) — 测试 vision+inline OCR 能力，评估替换 qwen3-vl:2b
2. 🟢 **MobileExplorer 并行探索** — 在 handler 推理期间加并行 UI 探测线程
3. 🟢 **unknown 场景 prompt 优化** — 301/672=45%，预期降至 30% 以下
4. ⚪ **Bonsai Image 4B** — 本地图像生成工具评估
