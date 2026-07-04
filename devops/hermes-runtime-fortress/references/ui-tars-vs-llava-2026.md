# UI-TARS vs LLaVA: 屏幕理解类任务选型决策 (2026-06-28)

## TL;DR

- **LLaVA + 自拼 JSON prompt ≠ UI 理解** — 幻觉率高, 颜色编码/按钮意图分类不准
- **UI-TARS-1.5-7B-MLX** (94% ScreenSpot-v2) 是当前 Mac mini 24GB 上屏幕 grounding 的**最优解**
- **不要写 `screen_understand.py` 类的自造轮子** — UI-TARS-desktop (37k stars, Apache-2.0) 已经是答案

---

## 一、为什么 LLaVA 不够用

实测场景: 一张企业微信在线文档表格截图, LLaVA 7B 自拼 prompt 输出:

```json
{
  "buttons": [
    {"label": "登录", "intent": "submit", "danger_level": 0},
    {"label": "注册", "intent": "submit", "danger_level": 0},
    {"label": "忘记密码?", "intent": "navigate", "danger_level": 0}
  ]
}
```

**问题**:
1. ❌ 把"在线文档表格"误识成"登录页" — 上下文判断能力弱
2. ❌ 颜色编码识别错: 把"延期"红块说成"绿色"
3. ❌ 表格结构理解错: 3 行说成 1 行, 单元格位置乱
4. ❌ "general" prompt 直接照抄 prompt 模板, 没真看图
5. ❌ 单卡 M4 GPU 不能并发, 5 路并发 30s, 串行 5 路 30s, 没省时间

**根因**: LLaVA 训练目标是"通用图像描述", **不是 UI grounding**。

## 二、UI-TARS 是什么

**UI-TARS** (Task Automation and Reasoning System) — ByteDance + 清华开源:

| 指标 | 数值 |
|---|---|
| License | Apache 2.0 |
| GitHub stars | 37.4k |
| Forks | 3.8k |
| Latest | v0.3.0 (2025-11) |
| Paper | arXiv:2501.12326 |

**两个产品**:
- **UI-TARS Desktop** (Electron app) — 直接装 .dmg, 配对模型就开用
- **Agent TARS** (CLI + Web UI, MCP 内核) — `npx agent-tars` 一行起

**模型版本**:
- UI-TARS-2B / 7B / 72B (1 月发布)
- UI-TARS-1.5-7B (4 月, 27.5% OSWorld, 94.2% ScreenSpot-V2)
- UI-TARS 2 (9 月, **47.5% OSWorld**, 532M 视觉编码器 + 23B 激活参数 MoE)

**vs Claude Computer Use**:
- OSWorld 47.5% vs 22.0% (**2x 强**)
- AndroidWorld 73.3% vs ~35% (**2x 强**)
- 完全本地, 0 美元/调用

## 三、Apple Silicon 部署路径 (本机实测)

### 为什么不用 Ollama

- ❌ `ollama pull ui-tars:7b` → "file does not exist" (Ollama Library 没收录)
- ❌ `ollama pull ui-tars-7b` → 同样失败
- ❌ Reddit 2025-01: "GGUF is currently not working. Right now the only way to serve it up locally is to use something like vllm"
- ❌ vLLM 要 16GB+ VRAM, Mac mini 24GB 统一内存勉强

### ✅ 正确路径: MLX + Rapid-MLX

```bash
# 1. 装推理引擎 (本机已测, ~3 分钟)
python3 -m pip install rapid-mlx
# 自动装 mlx / mlx-lm / mlx-metal, Apple Silicon Metal GPU 加速

# 2. 拉 UI-TARS-1.5-7B-MLX 模型 (~4GB, 5-10 分钟)
rapid-mlx pull ui-tars-1.5-7b-4bit
# 来自 mlx-community/UI-TARS-1.5-7B-4bit
# HuggingFace mlx-community 维护, production ready

# 3. 起 OpenAI 兼容 server
rapid-mlx serve ui-tars-1.5-7b-4bit
# 监听 :8000, OpenAI API 格式
```

### Rapid-MLX vs Ollama 性能对比 (官方 benchmark, M3 Ultra 256GB)

| 维度 | Ollama | Rapid-MLX | 加速 |
|---|---|---|---|
| Qwen3.5-4B 推理 (B=4) | 120 tok/s | **261 tok/s** | 2.18x |
| Qwen3.5-9B (B=4) | 84 tok/s | **180 tok/s** | 2.14x |
| GPT-OSS 20B (B=4) | 97 tok/s | **221 tok/s** | 2.29x |
| Cached TTFT | ~200ms | **80ms** | 2.5x |

**为什么 Rapid-MLX 快**: 直接用 MLX (Apple 原生矩阵运算) + 自己的 sampler, 不走 GGUF 转换层。

## 四、UI-TARS 输出格式与 Hermes 接入

UI-TARS 输出是**自然语言 + 坐标**, 不是 JSON:

```
Click on the "Login" button.
<action>click(450, 320)</action>
```

或 bounding box 形式:
```
{"bbox_2d": [344, 612, 478, 658]}
```

**接入步骤 (3 行, 不写代码)**:
1. `rapid-mlx serve` 启 server → `http://localhost:8000/v1/chat/completions`
2. Hermes 拿截图 → POST 给 server → 拿坐标
3. 坐标转 `mcp_cua_driver_click(x, y)` 完成操作

**已有 100% 兼容的 npm 工具 (直接装不写代码)**:
- `npm install -g browserground` — npm 全局装, 5 行 wrapper
- `npx agent-tars` — Agent TARS CLI, MCP 内核

## 五、什么时候用什么

| 任务 | 用什么 | 工具 |
|---|---|---|
| Chrome 内网页/表格/表单 | **通道 A: CDP DOM** | `browser_snapshot` / `browser_click` |
| Chrome 内复杂富文本/canvas | **通道 B: UI-TARS-MLX** (94% 准确) | Rapid-MLX server + 坐标 → click |
| macOS 原生 app (微信/QQ/钉钉) | **通道 C: AX 树** | `mcp_cua_driver_get_window_state` |
| 视频/游戏/自定义绘制 | **通道 D: 像素坐标 + UI-TARS 辅助** | `mcp_cua_driver_click(x, y)` |
| 跨应用/企业微信/H5 容器 | **通道 E: UI-TARS-MLX 屏幕 grounding** | Rapid-MLX + DOM fallback |
| 通用看图/描述 | LLaVA / Qwen-VL (云端或本地) | `vision_analyze` |

**铁律**: 屏幕 grounding 类任务 → **0 思考走 UI-TARS-MLX, 不写新 prompt**。

## 六、为什么自造 prompt 是反模式

Ponytail 6 步决策梯子的 step 4: "已装的依赖能解决? 用现成的"。

**用户原话 (2026-06-28)**: "记忆中有一条代码不要去乱写, 不要自我发挥, 一定优先选用各大网站论坛, 社区已经落地成熟的代码, 搜索各大社区成熟的代码获取过来, 而不是自己发挥"

**自造 prompt 的隐性成本**:
1. ❌ 训练集偏差: LLaVA 训练时没见过你的 UI
2. ❌ 提示词脆弱: 改一个字结果全变
3. ❌ 维护成本: 改一次 prompt 要重测所有场景
4. ❌ 单点失败: 一个 prompt 失效, 整个链路崩
5. ❌ 别人看不懂: 团队成员接手难
6. ❌ 社区版本更快: UI-TARS 团队每周发新权重, 你追不上

## 七、相关链接

- UI-TARS 官方: https://github.com/bytedance/ui-tars
- UI-TARS Desktop: https://github.com/bytedance/ui-tars-desktop
- MLX 版模型: https://huggingface.co/mlx-community/UI-TARS-1.5-7B-4bit
- Rapid-MLX: https://github.com/raullenchai/Rapid-MLX
- 综合指南 (2026-05): https://tosea.ai/blog/ui-tars-desktop-complete-guide-2026
- browserground: https://github.com/renezander030/browserground
- Agent TARS: https://agent-tars.com/