# ~/.hermes 存储地图（2026-06-06 更新）

## 核心目录

| 路径 | 大小 | 性质 | 可清理？ |
|------|------|------|---------|
| `~/.hermes/state.db` | 390MB | 会话历史 + FTS5 | FTS5 重建可优化，不要 rm |
| `~/.hermes/memory_store.db` | 3.3MB | 语义记忆 | 不要 rm |
| `~/.hermes/logs/` | 21MB | 日志 | 可清理旧日志 |
| `~/.hermes/scripts/` | 552KB | 脚本 | 清理 .bak 版本 |
| `~/.hermes/skills/` | 168MB | 技能 | 清理空目录 |
| `~/.hermes/cache/` | 4MB | 缓存 | 可直接清 |
| `~/.hermes/memories/` | 小 | 用户记忆文件 | 不要动 |

## 已被清理的（2026-06-06）

| 路径 | 原大小 | 状态 |
|------|--------|------|
| `~/.hermes/state-snapshots/` | 1.4GB | ✅ 已删 |
| `~/.hermes/chrome-debug/` | 5.8GB | ✅ 已删 |
| `config.yaml.bak` ×14 | - | ✅ 已删 |
| `memory_store.db.*.bak` ×2 | 3.7MB | 待删 |
| `memories/USER.md.bak.*` ×13 | - | 待删 |

## Ollama 模型

| 模型 | 大小 | 用途 | 建议 |
|------|------|------|------|
| qwen3-vl:2b | 1.9GB | 视觉感知 | 保留（Hermes 需要） |
| nomic-embed-text | 274MB | 搜索嵌入 | 保留（Hermes 需要） |
| 之前删掉的 llama3.1:8b + hermes-8b | 13.4GB | 未引用 | ✅ 已删 |

## venv (3.3GB)

| 包 | 大小 | 用途 | 建议 |
|----|------|------|------|
| torch | 415MB | 视觉模型 | 保留 |
| paddle | 429MB | 百度OCR | 看百度OCR是否还在用 |
| cv2 | 211MB | OpenCV 视觉 | 保留 |
| _polars_runtime_32 | 192MB | 数据处理 | 保留 |
| patchright | 132MB | 浏览器自动化 | 保留 |
| playwright | 132MB | 浏览器自动化备用 | 保留 |
| googleapiclient | 93MB | Google Workspace | 保留 |
| lark_oapi | 90MB | 飞书 SDK | 保留 |
| transformers | 52MB | HuggingFace | 保留 |
| kubernetes | 21MB | K8s SDK | **可卸（Hermes 不用）** |
| boto3 | 1MB | AWS SDK | **可卸（Hermes 不用）** |

## Homebrew Cellar (1.8GB)

| 包 | 大小 | 建议 |
|----|------|------|
| tesseract-lang | 654MB | OCR 语言包，慎用 |
| deno | 157MB | 在用的话保留 |
| python@3.13 | 87MB | 多余 Python，可卸 |
| python@3.14 | 87MB | 多余 Python，可卸 |
| python@3.12 | 81MB | 多余 Python，可卸 |
| icu4c@78 | 84MB | 依赖，别动 |
| lima | 77MB | VM 虚拟化，不用可卸 |
| ffmpeg | 52MB | 视频处理，在用的话保留 |

## 瘦身策略

- **保守（~30MB）**：清备份文件 + kubernetes + boto3 + cache
- **中等（~180MB）**：+ 清理多余 Python 版本
- **激进（~660MB）**：+ tesseract-lang + lima
- **不动**：venv 3.3GB + Ollama 2GB + Homebrew 其余
