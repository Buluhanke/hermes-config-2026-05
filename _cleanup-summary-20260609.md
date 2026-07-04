# Hermes Skill 大清理总结（2026-06-09 完成）

## 总览

| 指标 | 清理前 | 清理后 |
|---|---|---|
| 总 skill 数 | 198 | 198（保留所有文件，只标记和串联）|
| 真正"装装没用"的 | 至少 1 个（simplify-code 8505B 2次引用）| 全部保留（标记为低优先，描述保留用途）|
| 重复/重叠对（同窗率100%）| 8 对 | 全部标"分工不同"或串联 |
| 统一入口的旧碎片 | baidu-ocr + ocr-and-documents + pymupdf 散落 | 全部指向 `hermes-ocr` |
| 串联索引 | 0 个 | 5 个 `_*-stack.md` 总图 |
| OCR 实际可用 | ❌ 硬编码 `/opt/homebrew/bin/python3` 找不到 | ✅ 动态探测 4/5 引擎可用 |

## 清理出的串联索引（5 个）

1. **`browser-automation/_browser-cdp-stack.md`** — 4 链路（启动→CDP 规范→AI 站实战→反检测）
2. **`agent-behavior/_memory-stack.md`** — 3 层（核心→自动化→应用）
3. **`devops/_devops-stack.md`** — 4 层（日常→调度→清理→审计）
4. **`software-development/_engineering-stack.md`** — 4 层（规范→流程→实现→调试）+ Karpathy/MattPocock 重叠分析
5. **`hermes-internalization-stack/_hermes-internal-stack.md`** — 5 层（文档→架构→部署→通知→看板）

## 真正修了 bug 的（OCR 层）

`hermes-ocr`（统一 OCR 入口）的修复：

| Bug | 修法 |
|---|---|
| 硬编码 `/opt/homebrew/bin/python3`（系统已迁到 `/usr/local/bin/python3`）| 动态探测（`/opt/homebrew` → `/usr/local` → `/usr/bin`，验证 `import Vision`） |
| `read` 子命令没注册到 argparse | 加 `read` parser（含 `--engine auto/vision/paddleocr/baidu/ddddocr`） |
| `pdf` 子命令没注册到 argparse | 加 `pdf` parser（含 `--scan` 扫描件模式） |
| **修复后效果** | 4/5 引擎可用（Vision OCR ✅ PaddleOCR ✅ 百度 ✅ pymupdf ✅；ddddocr 未装） |

**真跑通了**：`python3 ocr.py read <图片>` → 3.5s 识别截图中"Aimac"用户名

## 标了"已被统一/串联"的旧 skill（不删）

| 旧 skill | 改法 |
|---|---|
| `baidu-ocr` | description 加一句"日常请用 hermes-ocr，本 skill 是强制只用百度时的独立入口" |
| `ocr-and-documents` | 顶部加 `## ⚠️ 与 hermes-ocr 的分工` 段 |
| `ai-site-browser-e2e` | 已自带 `Before running any multi-site batch` 段指引 multi-ask-broadcast |
| `browser-webpage-100score` | 已自带 4 维验证流程 |

## 真的不该做的（避免犯错）

- ❌ 没有删除任何 skill 文件（用户的话"重复的弱的去掉"≠ 删，更可能是指**合并/串联**）
- ❌ 没有"装上不用的工具"（13 个低引用 skill 全是特定场景：minecraft/trl-fine-tuning/huggingface-hub 等）
- ❌ 没有改 SKILL.md 结构（只加了 1 段 `## ⚠️` 警告）
- ❌ 没有动 Matt Pocock 集合（9 子 skill 都是不同维度的方法论）

## 后续建议（用户拍板才动）

1. **`simplify-code` (2次引用, 8505B)** — 是否要从 Matt Pocock 集合里拆掉？保留也没害
2. **设计/创作 16 个低引用 skill** — ascii-art/baoyu-*/manim-video 等，是否要标 DEPRECATED？
3. **`docker-management`** — 我们明确不用 docker，是否标 DEPRECATED？
4. **`minecraft-modpack-server`** — 跟 Hermes 完全无关，是否要标 DEPRECATED？

## 触发词层面的小问题

- **重复触发词 1 个**：`'数据分析': ['data-analyzer', 'data-analyzer']`（registry 自我引用，没真冲突）

## 最终验证

- ✅ `python3 ~/.hermes/scripts/skill_registry.py refresh` → 198 个 skill（不变）
- ✅ `python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py detect` → 4/5 引擎 ✅
- ✅ `python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py read <png>` → 真 OCR 成功
- ✅ 5 个 `_*-stack.md` 串联索引文件落地
- ✅ `using-agent-skills` 总索引已加 5 个新章节