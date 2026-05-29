# 2026-05-30 空闲学习记录（第二轮）

**学习方向**：执行层 — screen_watcher 存活验证 + Vision 模型现状确认

**搜索关键词**：Vocaela-500M GGUF Ollama import, qwen3-vl:4b Ollama availability

**核心发现**：
- **screen_watcher 链路验证完成** ✅：
  - 进程存活（PID 61102，11:58PM启动）
  - 截图正常（~/.hermes/screenshots/current.png，3.3MB，02:39）
  - handler触发正常（每~20秒一次分析）
  - dry-run日志正常（42条AUTO-EXEC-DRY记录）
  - 链路完整，无需干预
- **qwen3-vl:4b 在 Ollama 上不存在** — API返回not found，确认昨天实测结论，不要再尝试pull
- **Vocaela-500M 导入 Ollama 方式确认**：
  - 需要 GGUF 文件（Q8_0约437MB）+ mmproj 文件（109MB）
  - Ollama 当前版本不支持 MMPROJ 命令（GGUF只有语言权重，vision encoder在mmproj）
  - 需要 `brew install llama.cpp` 后用 `llama-cli -m GGUF -mmproj MMPROJ` 方式运行
  - 备选：Vocaela-2 已发布（3x faster），但只有safetensors无GGUF
- **Ollama 全量模型池（2026-05-30）**：qwen3-vl:235b（470GB），qwen3-vl:2b（1.9GB），gemma4:31b（62.5GB），gemma3:27b（55GB）等
- **本地已部署**：smolvlm2-agentic-gui（GUI专用，61.71% ScreenSpot）+ qwen3-vl:2b（通用，响应慢46.6s）
- **候选升级模型**：
  - llama3.2-vision:11b（~8GB，通用视觉强，M4 24G可跑）
  - blaifa/InternVL3_5:4B（3.4GB，基于Qwen3）— ⚠️ Mac Bug待修复（Issue #12166）
  - Holo1.5-3B（91.7%，需手动GGUF导入，M4 24G可跑）

**可执行改进**：
- screen_watcher链路已完整运行，维持现状
- 尝试拉取 llama3.2-vision:11b 测试通用视觉理解（对比smolvlm2的GUI专项）
- 关注 Holo1.5-3B GGUF 导入可行性（Ollama pull 500错误，需手动下载导入）

**下次学习方向**：Vision — llama3.2-vision:11b vs smolvlm2 实际GUI理解对比测试

**备注**：上次学习遗留问题"screen_watcher存活检查"已解决（2026-05-30实测：链路完整，42条dry-run记录）。本轮完成。