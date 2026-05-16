# 桌面全域 Agent — 成长路线图

> 来源：2026-05-14 与老板的类人化战略复盘

## 最终目标

**真人化数字劳动力**：像真人一样操作电脑/手机完成任何数字任务。

现状：我们是"浏览器实习生"——眼睛在Chrome里，双手被绑住。

---

## 技能树现状

### ✅ 已有（已验证可用）

| 层级 | 能力 | 工具 | 状态 |
|------|------|------|------|
| 感知 | 截图+OCR读屏 | Baidu OCR (1000次/月) | ✅ 已验证 |
| 感知 | CDP AX树读取 | Playwright CDP | ✅ 已验证 |
| 感知 | AppleScript窗口控制 | System Events | ✅ 已验证 |
| 感知 | 窗口尺寸/位置获取 | AppleScript | ✅ 已验证 |
| 执行 | 鼠标点击/拖/滚 | PyAutoGUI | ✅ 已安装 |
| 执行 | 键盘粘贴/按键 | cliclick | ✅ 已安装 |
| 执行 | CDP深度控制 | 原生WebSocket | ✅ 已验证 |
| 执行 | AppleScript窗口激活 | osascript | ✅ 已验证 |
| 架构 | 统一感知层 | unified-perception | ✅ 已构建 |
| 架构 | WorldState世界模型 | hermes-rpa/perception/ | ⚠️ 未完全集成 |
| 架构 | 5层验证器 | hermes-rpa/perception/ | ⚠️ 未完全集成 |
| 消息 | Telegram/QQ等 | Hermes Gateway | ✅ |

### ❌ 还没有

| 层级 | 能力 | 优先级 | 备注 |
|------|------|--------|------|
| 感知 | 屏幕变化检测（弹窗/新消息） | 高 | 不知道屏幕变了 |
| 感知 | 当前活动窗口追踪 | 高 | 不知道哪个窗口在前台 |
| 感知 | 桌面全域截图（不只是Chrome） | 高 | 只能截全屏像素 |
| 执行 | 操作桌面应用（Excel/Word/PDF） | 高 | 不会操控Chrome以外应用 |
| 执行 | 验证码对抗 | 高 | 遇到就卡死 |
| 业务 | 邮件读取/自动回复 | 高 | 只能发不能收 |
| 业务 | 微信/飞书消息读取 | 高 | 无法感知移动端 |
| 业务 | 多步骤任务可中断/恢复 | 中 | 断了要从头开始 |
| 记忆 | 老板画像/偏好持久化 | 中 | 每次从零开始 |
| 执行 | 本地VL理解截图（省百度OCR） | 低 | Ollama未装 |
| 架构 | n8n工作流编排 | 低 | 未部署 |

---

## 三层架构

```
用户指令（QQ/微信/Dashboard）
    ↓
① 感知层
   ├─ CDP AX树（浏览器内有结构）
   ├─ AppleScript AXUI（桌面窗口结构）
   ├─ 截图+OCR（像素级内容读取）
   └─ Screen/窗口变化检测 ← 缺口
    ↓
② 决策层
   ├─ Hermes (LLM) 理解 + 规划
   ├─ WorldState 世界状态累积
   ├─ ElementRegistry 操作历史追踪
   └─ 多步骤任务链（可中断/恢复） ← 缺口
    ↓
③ 执行层
   ├─ cliclick（鼠标键盘模拟）
   ├─ PyAutoGUI（桌面全域）
   ├─ CDP（浏览器内深度控制）
   └─ AppleScript（窗口管理）
```

---

## 下一步优先级（建议顺序）

### 第一优先级：打通感知→执行闭环

当前 `hermes-rpa/perception/` 已有完整模块（WorldState、Verifier、CoordinateTransformer），但没有真正跑通"截图→OCR→pyautogui点击"的端到端闭环。

**要做的事**：
1. 写一个 `desktop_agent_loop.py`：截图→OCR→找元素→pyautogui.click→验证→截图对比
2. 在 `fake_site/` 或真实页面上跑通（不用1688）
3. 验证 Mac Retina 坐标转换是否正确

**验收标准**：对任意屏幕区域截图，AI能找到目标元素并点击成功，验证通过。

### 第二优先级：屏幕变化检测

真人知道"弹窗来了"，AI不知道。需要：
- 定时截图 + hash对比（变化检测）
- 或 AXUI 窗口列表监听（新窗口出现）

### 第三优先级：桌面应用操作

用 PyAutoGUI + OCR，在非Chrome应用上完成一个完整任务。

示例任务：
- 打开Finder → 找到某文件 → 拖到桌面 → 截图确认

---

## 桌面Agent架构全景（reference补充）

```
hermes-rpa/perception/
├── schema/ui_object.py      # UIObject定义（10字段）
├── normalizers/
│   ├── ax.py              # Chrome AX Tree → NormalizedUIObject
│   ├── ocr.py             # Baidu OCR → NormalizedUIObject
│   └── yolo.py            # YOLO → NormalizedUIObject（可选）
├── fusion/merger.py        # IoU融合规则
├── resolution/
│   └── entity_resolution.py # 对象去重（IoU + text相似度）
├── world/state.py           # WorldState 世界状态
├── query/engine.py          # find_by_text / find_clickable / find_inputs
├── actions/click.py         # click(text) → pyautogui
├── verification/verifier.py  # 5层验证（URL→元素消失→hash→OCR→Vision）
├── diff/world_diff.py       # 结构变化检测
├── transform/coordinate.py  # viewport/screen/Retina坐标转换
└── drivers/mouse_driver.py # PyAutoGUI/CDP双驱动抽象

已安装工具：
- PyAutoGUI: ✅ 0.9.54（screen 1920×1080）
- cliclick: ✅ 已安装
- Baidu OCR: ✅ 已配置（AppID 7699346）
- OpenCV: ❌ 未安装
- Ollama: ❌ 未安装
```

---

## 核心原则

1. **能走API的走API**（n8n、飞书Webhook），走不了的才用视觉模拟
2. **感知先于执行**——每次操作前先看清楚再动手
3. **验证闭环**——每步操作必须有反馈（URL变化/元素消失/截图hash）
4. **相对坐标优于绝对坐标**——基于窗口尺寸比例计算，窗口resize后依然有效
