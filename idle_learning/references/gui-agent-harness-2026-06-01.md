# GUI-Agent-Harness（2026-06-01 发现）

**来源**：https://github.com/Fzkuji/GUI-Agent-Harness
**状态**：活跃开发（542 commits，最新 3 小时前），32 stars
**OSWorld Multi-Apps**：79.8% (72.6/91 evaluated tasks)

## 核心架构：4-phase step loop

```
gui_agent()
  ├── for step in 1..max_steps:
  │   ├── 1. Observe     (Python) — screenshot + detect + match + state ID
  │   ├── 2. Verify      (LLM)   — check previous action's result
  │   ├── 3. Plan        (LLM)   — decide next action
  │   └── 4. Dispatch    (Python) — execute: click/type/scroll/general
  │   └── build_step_feedback() → next iteration
  └── return result summary
```

最大亮点：**Verify 阶段** — Hermes auto_execute 缺失这一步（仅 scene classification，无 action 结果验证）。

## 关键特性

### Visual Memory
- UI 组件首次检测后：裁剪视觉模板（快速匹配）+ VLM 标签（推理用）
- 后续 template matching 替代 VLM 重检测（~5x faster, ~60x fewer tokens）
- 按 app 存储，跨 session 复用

### State Transitions
- UI 建模为 state graph（状态 = 可见组件集合）
- 成功动作序列记录为 transition，供未来 replay

### Provider-agnostic
- 支持 Claude Code CLI / OpenClaw / Anthropic API / OpenAI API
- 设计为 **LLM tool** — 被 LLM 作为 CLI 工具调用

### 平台
- macOS: Apple Vision OCR + pynput + Accessibility API（主力）
- Windows: Win32 API + EasyOCR（降级）
- Linux: wmctrl + xdotool + EasyOCR（降级）

## Hermes 对比

| 维度 | GUI-Agent-Harness | Hermes |
|------|------------------|--------|
| 定位 | CLI tool for LLMs | Per-user desktop companion |
| 感知 | GPA-GUI-Detector + OCR + template matching | qwen3-vl:2b scene classification |
| 循环 | 4-phase (O→V→P→D) | screen_watcher → handler → auto_execute |
| Verify | ✅ LLM 检查前一动作 | ❌ 缺失 |
| Memory | 视觉模板 + state graph | holographic 跨会话 |
| macOS | Apple Vision OCR | cliclick + screencapture |
| OSWorld | 79.8% Multi-Apps | N/A |

## 安装与使用

```bash
pip install openprogram
openprogram programs install gui

gui-agent --work-dir /tmp/workdir --app firefox "Open Firefox and go to google.com"
```

## 对 Hermes 的启发
1. 增加 **Verify 阶段** 到 auto_execute 流程（检查动作是否成功落地）
2. 采用 **visual memory 复用** 降低 handler 延迟（~5x faster）
3. CLI-as-tool 模式与 Skills 模式哲学一致
4. State graph 比当前"每次从零分析"更高效

## 限制
- 32 stars，非常早期
- 依赖 OpenProgram 宿主框架
- macOS grounding 依赖 Apple Vision OCR + template matching，无独立 VLM grounding
