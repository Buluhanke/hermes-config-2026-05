# InternVL3_5:4B Mac Bug — Issue #12166 状态更新（2026-06-02）

## Issue 原始信息
- **GitHub Issue**：https://github.com/ollama/ollama/issues/12166
- **报告内容**：`blaifa/InternVL3_5:4B` 在 Mac（macOS 15）上图片描述结果错误
- **受影响模型**：InternVL3_5:4B，其他模型正常（moondream、gemma3:4b、qwen2.5vl:3b 等）

## 2026-06-02 查询结果
- **Issue 状态**：已关闭（Closed 2025-09-03T17:53:46Z）
- **官方结论**：标记为 duplicate（重复问题）
- **最新评论**："Going to close this as a dupe."（关闭为重复issue）

## 结论
1. Issue 已关闭超过 8 个月（2025-09 → 2026-06）
2. 可能已在后续 ollama 版本修复
3. **建议**：可重新实测 InternVL3_5:4B 图片理解任务验证是否仍有问题
4. 如仍有问题，需开新 issue 并提供复现步骤

## 当前建议
- Mac 图片理解任务可尝试 InternVL3_5:4B（如仍有问题则回退 smolvlm2-agentic-gui）
- 继续用 smolvlm2-agentic-gui（61.71%，GUI专用，稳定）作为主力模型
- qwen3-vl:2b 作为场景分类专用模型（get_scene_type 任务）

## 参考
- GitHub Issue #12166：https://github.com/ollama/ollama/issues/12166
- Comment count: 2（最后一次评论即关闭通知）