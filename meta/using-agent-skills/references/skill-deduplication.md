# Skill 库精简对照表

> 2026-05-18 整理。归档到 `~/.hermes/optional-skills/`，可按需恢复。

---

## 🔴 高度重叠（选1~2个，删除其余）

### 代码补全（4选1）
| 文件 | 淘汰理由 | 建议保留 |
|------|---------|---------|
| `augment-code.md` | 最不知名 | ❌ 删除 |
| `tabnine.md` | 免费但不如 codeium 活跃 | ❌ 删除 |
| `amazon-codewhisperer.md` | AWS限定，场景窄 | ❌ 删除 |
| `codeium.md` | 免费，最活跃 | ✅ 保留 |

### SD WebUI（3选1）
| 文件 | 淘汰理由 | 建议保留 |
|------|---------|---------|
| `a1111-sd-webui.md` | 与 stable-diffusion-webui 功能99%重合 | ❌ 删除 |
| `invokeai.md` | SD变体，不如原版完整 | ❌ 删除 |
| `stable-diffusion-webui.md` | 最完整，用户最多 | ✅ 保留 |

### AI视频（7选2）
| 文件 | 淘汰理由 | 建议保留 |
|------|---------|---------|
| `zeroscope.md` | 效果偏弱 | ❌ 删除 |
| `haiper.md` | 社区相对小 | ❌ 删除 |
| `kling.md` | 保留 | ✅ 保留 |
| `pika.md` | 保留 | ✅ 保留 |
| `pixverse.md` | 保留 | ✅ 保留 |
| `morphstudio.md` | 3D视频差异化 | ✅ 保留 |
| `stable-video.md` | Stability官方 | ✅ 保留 |

### AI编程Agent（5选2）
| 目录 | 淘汰理由 | 建议保留 |
|------|---------|---------|
| `openhands/` | Docker部署偏重 | ❌ 删除 |
| `smol-agents/` | 框架不够成熟 | ❌ 删除 |
| `agno/` | pydantic-ai 覆盖更广 | ❌ 删除 |
| `openghost/` | 轻量+浏览器自动化强 | ✅ 保留 |
| `voyager/` | Minecraft专项，无替代 | ✅ 保留 |

### 本地LLM推理（已用Ollama）
| 目录 | 淘汰理由 | 建议保留 |
|------|---------|---------|
| `llama-cpp/` | Ollama已覆盖，无需手动管理 | ❌ 禁用 |
| `serving-llms-vllm/` | Ollama已覆盖 | ❌ 禁用 |

---

## 🟡 中度重叠（合并或二选一）

| 组 | 文件 | 操作 |
|----|------|------|
| Git工作流 | `git-workflow.md` + `git-workflow-and-versioning.md` | 合并到 `git-workflow-and-versioning` |
| Web研究 | `web-research.md` + `deep-research.md` | 合并，保留 `deep-research`（更完整）|
| MCP协议 | `mcp-deep-dive/` + `mcp-server-build/` + `native-mcp/` | 合并为 `mcp/` 一个目录 |
| 元技能 | `skill_01~10/*.md`（10个） | 合并成 `meta-skills.md` |
| 计划 | `plan.md` + `planning-and-taYOUR_API_KEY.md` + `writing-plans.md` | 保留 `planning-and-taYOUR_API_KEY` |

---

## 🟢 各有独特价值（不剔除）

- `1688-automation` / `1688-procurement` — 业务核心
- `hermes-vision-agent` / `hermes-voice-module` / `hermes-humanization-core` / `hermes-memory-hpc` — Phase核心能力
- `procurement/` — 8个采购子技能，各有分工
- `claude-code-architecture` / `claude-code-architecture-deep-dive` — 源码研究
- `dogfood` — Web QA专项
- `sourcegraph-cody` — 代码库问答专项
- `tts` — 通用语音合成

---

## 精简目标

从 118 个 → 约 50~60 个有效技能，消除目录膨胀和选择困难。
