# Direction D — 执行层深度分析（2026-06-01）

## 分析背景
cron idle_learning 轮次，方向 D 执行层。无用户在场，系统稳定期深夜巡检。

## 关键发现

### DRY_RUN 状态
- `DRY_RUN = True`（screen_trigger_handler.py 第74行）
- 990 条 dry-run 记录，0 次真实执行
- **即使改为 False，实际效果仍为 "none"** — 因当前场景分布 99%+ 为 idle/other

### Action Whitelist（当前）
```
browser  → wininfo     wechat  → wininfo     1688 → ocr
dingtalk → wininfo     telegram → wininfo
desktop  → none        calculator → none     other → none     unknown → none
```

### Jun 1 真实执行分布
| Action | Scene | Count | 说明 |
|--------|-------|-------|------|
| none | other | 230 | 02:53~06:55 深夜静默 |
| none | unknown | 15 | 零星未知场景 |
| none | desktop | 9 | 清晨桌面场景 |
| wininfo | browser | 1 | 00:49 唯一一次业务场景 |

**结论**：99%+ 流量在 idle/other → 全部 none。动作多样性 = 0。

### 备份对比（关键！）
旧的 handler（2026-06-01 00:24 备份）的 whitelist 全部是 `wininfo`（包括 desktop/other/unknown → wininfo）。当前版本（02:53 后）改为 idle→none，日志噪声大幅下降。

### 坐标映射链
`get_scene_type()` 仅做 scene classification（单标签输出），不输出归一化坐标。`nclick` 依赖 Qwen3-VL 坐标 → 映射链未接线。

### RPA 动作差距
| 可用动作 | handler 调用 | 状态 |
|---------|-------------|------|
| ocr | ✅ (从未触发) | 1688 场景 0 次 |
| wininfo | ✅ | browser/wechat 极罕见 |
| click x,y | ❌ | 依赖坐标映射链 |
| nclick nx,ny | ❌ | 坐标映射链未接线 |
| type | ❌ | 无对应场景 |
| press | ❌ | 无对应场景 |
| openurl | ❌ | 无对应场景 |
| send | ❌ | 无对应场景 |
| readchat | ❌ | 无对应场景 |
| scroll | ❌ | 无对应场景 |

## DRY_RUN=False 前置条件检查表
| # | 条件 | 状态 | 判定 |
|---|------|------|------|
| ① | 至少一类业务场景稳定识别 | ❌ browser/wechat 极罕见，1688/dingtalk 0次 | 关键瓶颈 |
| ② | wininfo 仅限业务场景 | ✅ browser/wechat→wininfo，idle→none | 通过 |
| ③ | RPA 脚本存在 | ✅ hermes_desktop_rpa.py 存在 | 通过 |
| ④ | 深夜无误触发 | ✅ idle/other→none | 通过 |
| ⑤ | 日志跟踪 >24h | ✅ 连续 dry-run 记录 | 通过 |
| ⑥ | 回滚方案 | ❌ 备份存在但未测试恢复 | 待完成 |

## 可执行改进（无紧急项）
1. ✅ DRY_RUN=True 当前正确状态 — 业务场景不足时切换无意义
2. 业务场景 >5次/h 时可评估切换
3. 坐标映射链若启用，需在 scene classification 后接坐标提取
4. 准备回滚脚本：`cp .bak.20260601_0138 handler.py`

## 下次方向
方向B — GUI grounding 论文追踪（间隔已过 2 轮）
