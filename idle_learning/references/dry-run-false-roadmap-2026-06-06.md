# DRY_RUN=False 执行层改造路线图

**日期**: 2026-06-06 22:30
**状态**: Phase 1 已完成, Phase 2 待验证

## 现状

handler.py `get_scene_type()` 仅返回场景单词字符串，不输出 bbox 坐标 → 坐标系断裂 → auto_execute 无法精准点击。

## DRY_RUN=False 6 项前置条件评估

| # | 条件 | 当前状态 | 评估 |
|---|------|---------|------|
| ① | 业务场景稳定识别 | unknown 84% | ❌ 主要阻塞 |
| ② | wininfo 动作正确 | 映射正确 | ✅ |
| ③ | RPA 路径存在 | 16 defs | ✅ |
| ④ | 非 busy hours 不误触发 | 修复后无复发 | ✅ |
| ⑤ | 日志跟踪成熟 | dry-run 日志连续 | ✅ |
| ⑥ | 回滚方案测试 | bak 文件存在 | ✅ |

仅 3/6 通过 → **不可行**，但路线图可以逐步改善。

## 5 阶段路线图

### Phase 1: 扩大场景分类 ✅ 已实现
- **改动**: handler.py `get_scene_type` v2 新增 chrome/firefox/vscode/finder/terminal 等 14 个场景
- **效果**: 更多场景能区分，降低 unknown 率

### Phase 2: OCR 返回 bbox 坐标 🔧 已编码待验证
- **改动**: `ocr_get_text_with_rects()` 调用百度 OCR，返回 `{"text": "...", "left": x, "top": y, ...}`
- **效果**: 每个场景有具体元素坐标，auto_execute 可精准操作
- **关键**: 百度 OCR 免费额度 1000次/天（基础版），足够日常使用
- **风险**: OCR 对非文字元素（图标、按钮图形）无效

### Phase 3: 场景 → 动作映射表
- **改动**: 扩展 ACTION_WHITELIST，每个场景 + bbox 组合映射具体 RPA 动作
- **效果**: 已知场景 + 有坐标 → 自动执行

### Phase 4: 验证层
- **改动**: auto_execute 结果回写日志，记录执行成功/失败
- **效果**: 可衡量 DRY_RUN=False 的实际效果

### Phase 5: DRY_RUN=False 切换
- **条件**: unknown 率 < 30% + Phase 2-4 验证通过
- **风险**: 未知场景误操作 → 必须保留 human-in-the-loop 兜底

## 已知限制

1. **qwen3-vl:2b 不出坐标**: 测试多次确认 — 纯文本问答正常，bbox prompt 返回空 → 必须用 OCR
2. **百度 OCR 免费额度**: 1000次/天，足够但需监控
3. **OCR 精度**: 对模糊/小字/非标准字体精度下降
4. **屏幕分辨率依赖**: bbox 坐标与分辨率绑定，换分辨率后需重新校准

## 验证步骤（Phase 2 完成后）

1. `grep "get_scene_type" ~/.hermes/logs/screen_trigger.log | tail -20` — 确认返回 `{scene, elements, element_count}`
2. 手动触发一次屏幕变化，检查 log 输出
3. 检查 elements 列表中的 rect 值是否合理（x, y 在屏幕范围内）
4. 测试 auto_execute 是否能用 elements 中的 bbox 做精准点击
