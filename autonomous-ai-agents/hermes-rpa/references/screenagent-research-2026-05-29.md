# ScreenAgent 架构调研 — vision→action 闭环参考模板

**来源**: IJCAI 2024 论文 + GitHub: niuzaisheng/ScreenAgent
**调研时间**: 2026-05-29
**关联方向**: Direction D — 执行（手眼配合）

## 核心架构

ScreenAgent 的核心是 **planning-acting-reflection** 三阶段循环，这是 Hermes 当前 vision→action 断链的最直接参考模板：

```
用户任务
    ↓
┌──────────────────────────────────────────────┐
│ PLANNING 阶段                                  │
│ VLM 将用户任务拆解为子任务序列                   │
│ 例: "发送邮件" → [打开浏览器, 登录邮箱, ...]     │
└──────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────┐
│ ACTING 阶段                                    │
│ ① 观察截图 → 理解当前屏幕状态                    │
│ ② VLM 给出具体鼠标/键盘动作 + 坐标               │
│ ③ 控制器执行动作 (click, type, scroll)          │
└──────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────┐
│ REFLECTION 阶段                                │
│ ④ 再次截图 → 观察执行结果                        │
│ ⑤ 判断状态: 继续 / 重试 / 调整计划               │
└──────────────────────────────────────────────┘
    ↓
循环直到子任务全部完成
```

## 与 Hermes 的对比

| 维度 | ScreenAgent | Hermes (当前) |
|------|-------------|---------------|
| Planning | VLM 拆解任务 | 💡 缺 — 无任务规划层 |
| Acting | VLM 定位+控制器执行 | ✅ CDP 9222 可用 |
| Reflection | 截图对比验证 | ⚠️ 部分 — screen_poller 只检测变化，不验证执行 |
| 动作集 | click/type/scroll/hotkey | ✅ cliclick 可用 |
| 屏幕感知 | 截图+VLM 分析 | ⚠️ smolvlm2 可用 (5.8s) 但未接入动作循环 |
| 验证循环 | 每步必 verify | ❌ 缺 — 操作后不验证 |

## ScreenAgent 的关键设计

### 1. 结构化 Action Schema
ScreenAgent 使用固定的动作集合，每个动作有明确的参数和返回值：
- `click(x, y)` / `double_click(x, y)` / `right_click(x, y)`
- `type_text(text)` — 在焦点元素输入
- `scroll(direction, amount)`
- `hotkey(keys)` — 快捷键组合
- `screenshot()` → 返回截图用于验证

### 2. 屏幕坐标归一化
- VLM 输出归一化坐标 (0~1)
- 控制器乘以实际分辨率 → 屏幕坐标
- 好处：分辨率变化不影响 VLM 输出

### 3. Reflection 验证策略
- 执行前：截图保存当前状态
- 执行后：再次截图 → VLM 判断是否发生变化
- 变化了 → 成功，继续下一子任务
- 没变化 → 重试最多 N 次
- 错误状态 → 调整计划

## 对 Hermes 的启示

1. **screen_poller.py 可以扩展为 Acting 层**：当前只检测触发 → 通知，可以改为检测触发 → 截图 → VLM 分析 → 执行动作 → 验证
2. **smolvlm2 的 5.8s 响应足以支撑单次动作循环**：截图→分析→执行→验证 约 15-20s 一次
3. **Hermes 已有的 CDP 9222 链路可以替代 ScreenAgent 的截图模拟**：用 CDP Runtime.evaluate 替代纯视觉定位 + cliclick 替代控制器
4. **可以先用简单的 Action Schema 测试闭环**：`[click(x,y), verify_by_screenshot()]` 即可测试最基本的 vision→action 循环

## 参考链接
- 论文: https://www.ijcai.org/proceedings/2024/0711.pdf
- GitHub: https://github.com/niuzaisheng/ScreenAgent
