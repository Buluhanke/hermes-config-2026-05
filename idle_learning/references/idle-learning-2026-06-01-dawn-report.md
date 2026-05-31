# 2026-06-01 黎明离线巡检报告

## 时间
2026-06-01 ~05:00（cron 触发）

## 网络状态
github: blocked | hn: blocked — 完全离线

## 巡检结果

### 产线健康
- screen_watcher: PID 8748, 运行中, 截图 04:46 新鲜
- Ollama: qwen3-vl:2b loaded, 2.7GB, 4096 context, 100% GPU
- Handler: 正常循环, 否定检测生效, 锁文件无残留
- Handler仍在运行: 0 次

### 场景分布（当日 June 1 00:06~04:46）
- **other**: 246 (98.8%) — 全部正确 [silent]
- **unknown**: 2 (0.8%) — 历史最低
- **browser**: 1 (0.4%)
- **当日 unknown 率 0.8%**（全量历史 unknown 36% — 历史污染差异显著）

### 性能数据（产线实测时序）
- get_scene_type: ~3s
- ask_screen: ~5s
- 完整周期: ~8s（含冷却检查、日志、cooldown）

### is_dark_screenshot()
- 历史总触发次数: **0**（843+ dry-run 从未触发）
- 阈值 <500 字节过严；暂不修复（低 ROI）

### Hook 污染
- screen_watch gateway.log 条目: 1692（历史遗留，events:[] 后不再增长）
- HOOK.yaml 已正确置空

## 可执行改进
1. screen-watcher-vision SKILL.md 更新（已完成）：定时数据、场景分布、DRY_RUN 条件评估
2. idle_learning SKILL.md 更新（已完成）：暗屏检测局限、handler 性能数据
3. is_dark_screenshot 检测门槛暂不修改（验证结论：低 ROI）
