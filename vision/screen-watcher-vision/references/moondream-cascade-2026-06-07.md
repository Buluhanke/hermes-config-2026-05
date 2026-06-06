# moondream Cascade 场景分类架构（2026-06-07 发现 → 2026-06-04 验证）

## 背景问题
qwen3-vl:2b 当前承担所有视觉分析（场景分类 ~24s），是实时监控链路的主要延迟瓶颈。

## moondream 作为快速初筛器

**候选模型**：`moondream:1.8b-v2-q4_K_M`（Ollama registry 名字，pull 后显示 `moondream`）
- 大小：~1GB（Q4_K_M 量化）
- Ollama：直接 `ollama pull moondream` 可用
- 理论速度：M4 上 ~30+ tok/s（纯 decode，不含图像编码）
- 同 smolvlm2 量级，轻量视觉理解

## 2026-06-04 实测结论：❌ 不推荐作为 cascade 初筛器

**实测环境**：vision_understand.py + ollama moondream（同张 1.3MB 终端截图，多次运行）

| 维度 | moondream | qwen3-vl:2b |
|------|-----------|-------------|
| 推理耗时 | 0.7-3.6s（不稳定）| 23-30s（稳定）|
| 中文 prompt 响应 | **忽略中文**（即使用 "用一句话中文描述" prompt，仍返回英文）| 完美中文 |
| 区分相似图能力 | **疑似缓存/幻觉**（两张不同图返回完全相同英文描述）| 正常区分 |
| 中文场景点名（"hermes-agent"、"Ollama"）| 含糊（"foreign language"）| 精确 |
| 适用性 | ❌ 中文场景不可用 | ✅ 产线稳定 |

**实测 prompt 与输出**（同一张 1.3MB 终端截图）：
- prompt：`用一句话中文告诉我这张屏幕截图画的是什么内容。`
- moondream 输出：`The image shows a computer screen with three windows open. The first window displays a code or programming language, the second window has a text document, and the third window is empty.`
- qwen3-vl:2b 输出：`电脑屏幕显示多个窗口，左侧为运行Python代码的终端界面（含hermes-agent相关命令），中间和右侧是Hermes Agent工具的聊天界面及配置提示信息。`

**结论**：moondream 在中文 screen-watcher 场景**不适用**，cascade 架构不成立。

## 替代方案（待定）

要降低 qwen3-vl:2b 的 23-30s 延迟，可考虑：
1. **降低分辨率到 224×224**（screen-watcher 当前 400px，可再降）
2. **加 num_ctx 限制**（vision_understand.py 当前未设 num_ctx，吃 262144 默认值）
3. **改用更小 VLM**（如 llava:7b 中文也不强，smolvlm2 已下线）
4. **YOLO 预分类扩展**（当前 idle 旁路已省 50% 时间，uncertain 旁路可再加）

## 状态

- moondream **已实测，不推荐**
- 旧 cascade 假设作废
- 中文 screen-watcher 仍以 qwen3-vl:2b 为唯一选择，延迟靠 num_ctx + 分辨率优化
