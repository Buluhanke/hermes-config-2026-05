# CAPTCHAs 检测 AI Agent — auto_execute 安全须知（2026-05-30）

## 来源

- **论文**：Roundtable Research（roundtable.ai），CogCAPTCHA30，2026-05-27
- **链接**：https://research.roundtable.ai/captchas-detect-ai/

## 核心结论

Claude/GPT/Gemini 等前沿模型在**行为过程**上与人类差距大（小模型更接近人类）。
CAPTCHA 检测的是行为过程特征，不只是输出结果。

## 对 auto_execute 的影响

### 当前状态（DRY_RUN=True）
✅ 不受影响 — 只记录不执行，无真实行为暴露

### 切换到 DRY_RUN=False 后需考虑

**可被检测的行为特征**：
1. 鼠标移动轨迹（直线 → 暴露 bot）
2. 点击间隔（过于均匀 → 暴露 bot）
3. 键盘输入节奏（无自然停顿 → 暴露 bot）
4. 屏幕变化后响应延迟（规律性强 → 暴露 bot）

**Anti-CAPTCHA 对策**：
1. **轨迹扰动**：`cliclick mvpox,ypox` 操作前加随机微小移动
2. **延迟随机化**：`sleep` 加 ±30% 随机波动
3. **mouseMoved 前置**：macOS CGEventTap 要求前面有 mouseMoved 事件才接受 click
4. **过程级伪装**：不只是伪装输出，而是伪装完整行为链

### 安全检查点

在 `auto_execute()` 开启真实执行前，评估：
1. 当前场景是否有 CAPTCHA（检测页面元素）
2. 目标应用是否对 bot 行为敏感（金融/社交/账号操作）
3. 已有对策：延迟随机化、轨迹扰动

## 参考

详见 `idle_learning/references/captchas-detect-ai-agent-2026-05-30.md`