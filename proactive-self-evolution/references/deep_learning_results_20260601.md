# 深度学习结果归档（2026-06-01凌晨补充）

## 本轮新增发现

### 第5-6轮自优化结果

**搜索方向**: vision / cua / anti-captcha / 1688 / agent

**有价值发现**:

| 项目 | Stars | 描述 |
|------|-------|------|
| macOS26/Agent | 448 | Mac AI harness, 18+ providers |
| qdore/application-use | 6 | macOS原生自动化CLI |
| PercivalLin/jcbot | 3 | TypeScript macOS agent |
| deepanmpc/COWORK_AGENT_DESKTOP_AUTOMATION | 1 | PyAutoGUI+Playwright多模态Agent |
| nullvoider07/the-eyes | 1 | 跨平台屏幕抽象层 |
| 2captcha/mcp-captcha-solver | 4 | MCP captcha bypass |
| EvanTenenbaum/hermes-agent-self-evolution | 0 | Hermes self-evolution fork |
| EvanTenenbaum/hermes-self-evolution | 0 | DSPy+GEPA patched fork |

### 真人化组件验证（2026-06-01凌晨）

已验证全部通过：
- `hermes_agent_loop.py` ✅ 完整闭环演示成功
- Reflection机制 ✅ 3轮失败→反思→成功
- VLM视觉校验 ✅ qwen3-vl:2b验证通过
- DynamicWait ✅ 200ms轮询
- HumanTrajectory ✅ 贝塞尔曲线

### 浏览器感知层验证（2026-06-01凌晨）

**关键发现**: Vision OCR无法截取Chrome内内容（GPU合成限制）

| 方案 | 结果 | 结论 |
|------|------|------|
| screencapture + Vision OCR | 空白 | Chrome GPU层阻止 |
| browser_snapshot(DOM) | ✅ 8ms读取 | 主要感知方案 |
| browser_click/type | ✅ 正常 | 执行层完全正常 |

**闭环可完全依赖DOM感知**:
```
browser_snapshot(DOM) → LLM决策 → browser_click/type执行
```

## 历史归档
- `ai_agent_human_like_skills.md` — Gemini+豆包多平台建议汇总
- `ai_agent_evolution_gemini_advice.md` — 第一轮Gemini建议
- `self_optimization_findings_20260530.md` — 第1-4轮发现
