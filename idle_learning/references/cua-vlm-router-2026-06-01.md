# Cua VLM Router — 生产级 VLM 三分类路由（2026-06-01 调研）

来源：browser_navigate → cua.ai/docs/cua/guide/fundamentals/vlms + /cua-vlm-router

## 核心架构

Cua 提供统一的 VLM Router API，单一 key 访问所有模型：

```python
from cua import Sandbox, Image, ComputerAgent
async with Sandbox.ephemeral(Image.linux()) as computer:
    agent = ComputerAgent(
        model="cua/anthropic/claude-sonnet-4.5",
        tools=[computer]
    )
export CUA_API_KEY="your-cua-key"
```

**HTTP API**：同时兼容 Anthropic Messages 和 OpenAI Chat Completions 格式：

```bash
# Anthropic 格式
curl -X POST https://inference.cua.ai/v1/messages \
  -H "Authorization: Bearer $CUA_API_KEY" \
  -d '{"model": "anthropic/claude-sonnet-4.5", ...}'

# OpenAI 格式
curl -X POST https://inference.cua.ai/v1/chat/completions \
  -H "Authorization: Bearer $CUA_API_KEY" \
  -d '{"model": "microsoft/fara-7b", ...}'
```

## 模型三分类

这验证了 AVR 论文（CVPR 2026）的三层级联路由概念已落地生产：

### Full Computer-Use（全桌面控制）
| 模型 | 说明 |
|------|------|
| Claude (all versions) | 推荐全能型 |
| OpenAI computer-use-preview | 备选 |
| UI-TARS (ByteDance) | **M4 24GB 可本地运行** |
| Qwen 2.5 VL (Alibaba) | **M4 24GB 可本地运行** |

### Browser-Only（浏览器自动化）
| 模型 | 说明 |
|------|------|
| Gemini 2.5 Computer-Use | 浏览器专项优化 |
| Fara (Microsoft) | 浏览器专项优化 |

### Grounding-Only（仅 UI 定位，需组合 planner）
| 模型 | 说明 |
|------|------|
| GTA1 | 定位 |
| OmniParser (Microsoft) | UI 元素检测 |
| Moondream3 | 轻量定位 |

## Hermes 映射分析

当前 Hermes 使用的模型：
- **qwen3-vl:2b** → 属于 Full Computer-Use 类别但参数最小（2B）
- 可升级路径：UI-TARS 1.5 7B（Cua 官方推荐本地模型，~6GB Q4_K_M）

Cua 的分类体系与 AVR 论文的路由框架完全对应：
- 简单场景（~45%）→ Grounding-Only 模型足够
- 中等场景（~30%）→ Browser-Only 或小 Full CU 模型
- 复杂场景（~25%）→ 全能力 Full CU 模型

**对 DRY_RUN=False 切换的意义**：
- 当前 qwen3-vl:2b 覆盖简单~中等场景
- 暂无 AVR 式路由逻辑（全部走同一模型）
- 可考虑将 SafeGround 不确定性分数作为 routing 的触发器

## 关键限制

- Cua VLM Router 需付费 API key
- 但 **routing 架构思路可免费复用**：分类体系 + 置信度探测 + 模型升级无需 Cua 基础设施
- 本地备选：Ollama 多模型 + SafeGround 不确定性分数
