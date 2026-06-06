# 深度夜学 2026-06-06 完整日志

**开始时间**: 2026-06-06 22:30
**结束时间**: 2026-06-06 23:30
**方向**: D → A → B → C（完整循环，深度分析模式）
**模式**: 深度分析（非浅巡检）

## 方向 D — 执行层 ✅

### 核心发现
1. handler.py 404 行源码逐行读完，RPA 脚本 430 行 24 函数清单拉完
2. **核心阻塞**: 坐标系断裂 — `get_scene_type()` 只返回单词，不输出 bbox → 没法精准点击
3. **根因**: qwen3-vl:2b 有图能识别元素文本，但 bbox prompt 返回空 → VLM 不出坐标
4. **3612 次触发中 YOLO 过滤率 99.1%**，但 active=0 异常（阈值 >5 太高）
5. DRY_RUN=False 评估: 3/6 条件通过 → 不可行，但有 5 阶段路线图

### 已执行改造
- ✅ **Phase 1**: handler.py `get_scene_type` 扩展 14 个场景分类（chrome/firefox/vscode/finder/terminal）
- ✅ **Phase 2**: 新增 `load_ocr_config()` + `ocr_get_text_with_rects()` — 百度 OCR 获取文字坐标
- ✅ **Phase 2**: 改写 `get_scene_type()` 为 v2 混合方案（OCR + VLM 合并输出 `{scene, elements, element_count}`）
- ✅ **Phase 2**: `auto_execute()` 接收 `elements` 参数
- ✅ 备份 handler.py.bak.20260606

### 验证步骤
- 语法检查 ✅ 通过
- 等待下次 screen_trigger 实际运行验证 OCR + VLM 合并结果

## 方向 A — 视觉产线 ✅

### 核心发现
- Ollama 健康（PID 1264），qwen3-vl:2b 已加载
- 129 个不同 VLM 回答，夜间模板化正常
- 业务场景能正确识别 1688 通知
- 截图 1920x1080，current.png 8.5h 前更新
- **结论**: 产线健康，无紧急改进项

## 方向 B — 论文扫描 ✅

### 核心发现
- **Mano-P**: M4 Mac mini 本地运行，OSWorld specialized #1（58.2%）
- **UI-Venus 1.5**: 1.5/8B/30B-A3B 三规模，ScreenSpot-Pro SOTA
- 四篇 3/30 arXiv 同时提出不同 grounding 方法
- **建议后续**: 下载 Mano-P 实测

## 方向 C — 安全 ✅

### 已有发现（18:00 轮已完成）
- Microsoft Taxonomy v2.0 7 个失败模式分析
- 重点映射: Inter-Agent Trust Escalation（HIGH）+ Goal Hijacking（HIGH）

## 学习产出

### 代码修改
- `~/.hermes/scripts/screen_trigger_handler.py`: 404→552 行，新增 3 个函数，改 2 个函数签名

### Reference 文件
- `references/dry-run-false-roadmap-2026-06-06.md` — DRY_RUN=False 5 阶段路线图
- `references/ocr-vlm-hybrid-coordinate-extraction-2026-06-06.md` — OCR+VLM 混合方案技术笔记
- `references/direction-a-vision-line-deep-analysis-2026-06-06.md` — 视觉产线深度分析

### 技能更新
- `idle_learning/SKILL.md`: 添加"🆕 2026-06-06 深度夜学成果"条目

## 下一步优先级

1. **Phase 2 验证**: 等下一次 screen_trigger 触发，确认 OCR+VLM 合并输出正常
2. **Mano-P 下载**: 尝试下载 Mano-P 到 M4 本地测试（约 400MB）
3. **DRY_RUN=False 路线图 Phase 3**: 场景→动作映射表
4. **Cron 重新启用**: 考虑把 idle_learning 加回 cron（当前是手动跑）
