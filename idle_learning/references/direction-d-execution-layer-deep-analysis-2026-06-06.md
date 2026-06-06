# 方向 D 深度分析 — 执行层能力全面评估

**日期**: 2026-06-06 22:30
**范围**: handler 源码 + RPA 脚本 + 日志质量 + 坐标系 + DRY_RUN=False 路线图

## 1. 架构概览

```
screen_watcher (screencapture)
    ↓ 屏幕变化 → TRIGGER_FILE
handler.py on_trigger()
    ↓ 暗屏检测
YOLO ScreenParser 预分类 (idle/active/uncertain)
    ↓ idle→跳过, active/uncertain→
qwen3-vl:2b 场景分类 (9类)
    ↓ 场景 → VLM 问答
关键词匹配 urgency (silent/normal/urgent)
    ↓
auto_execute (DRY_RUN=True)
    ↓
Telegram 推送 (urgent/normal)
```

## 2. handler 源码深度分析 (404 行)

### 2.1 优点
- **YOLO 预分类**：ScreenParser YOLO 快速过滤 idle（0-1 元素），节省 VLM 调用
- **冷却机制**：60s 冷却 + handler lock，防止重复触发
- **暗屏检测**：is_dark_screenshot 快速过滤锁屏/黑屏
- **分级 urgency**：urgent/normal/silent 三级，减少噪音推送
- **否定检测**：unknown/other 场景下排除"没有错误"等否定上下文

### 2.2 关键缺陷

#### 缺陷 1：坐标映射链断裂 ❌
- `get_scene_type()` 只返回**场景分类单词**（如 "browser"、"desktop"）
- **不输出任何坐标、bounding box、元素索引**
- 无法做精准点击/操作，只能做 `auto_execute` 里的 `wininfo`/`ocr`（通用操作）
- Hermes RPA 脚本支持 `click x,y`、`nclick nx,ny`、`type`、`press`，但 handler 不传坐标

#### 缺陷 2：场景分类只有 9 类 ❌
- 缺少 `chrome`（与 browser 重叠？）、`vscode`、`finder`、`terminal`
- 分类 prompt 硬编码在代码里（line 209），不可配置
- `unknown` 场景占比极高（今天 26/31 条分析日志都是 unknown）

#### 缺陷 3：无备份文件 ❌
- `handler.py.bak.*` 全部缺失
- 无法回滚到已知稳定版本

#### 缺陷 4：auto_execute 过于简单 ❌
- 每个场景只映射到**单一动作**（wininfo/ocr/none）
- 没有多步操作能力
- DRY_RUN=True 时完全不做任何事情

## 3. RPA 脚本分析 (hermes_desktop_rpa.py, 430 行, 24 个函数)

### 3.1 已实现动作
| 动作 | 实现 | 依赖 |
|------|------|------|
| wininfo | get_chrome_window | AppleScript AXUI |
| ocr | screenshot + Baidu OCR | 百度 API + access_token |
| screenshot_region | sips 截图 | macOS sips |
| click x,y | cliclick c:x,y | cliclick CLI |
| nclick nx,ny | 归一化坐标转像素 | 同上 |
| type | 粘贴文字 | paste_text (AppleScript) |
| press key | cliclick kp:key | cliclick CLI |
| scroll | cliclick scroll | cliclick CLI |
| chrome_open_url | 浏览器打开 | AppleScript |
| chatgpt_send | ChatGPT 对话 | 自定义 |

### 3.2 缺失能力
- ❌ 无 `drag` 动作（拖拽）
- ❌ 无 `right_click` 动作
- ❌ 无 `double_click` 动作
- ❌ 无 `wait_for_element` 动作
- ❌ 无 `tab_switch` 动作
- ❌ 无 `paste_text` 组合键支持（只支持单键）
- ❌ 无 `find_element_by_text` 动作（OCR 只能全截图 OCR，不能指定区域找文字）

## 4. 日志质量分析

### 4.1 数据量
- 今天 handler 触发 3612 次（YOLO 预分类日志）
- VLM 实际调用仅 31 次（YOLO 过滤掉了 3581 次 idle）
- **YOLO 过滤效率：99.1%** ✅

### 4.2 场景分布（今天）
- unknown: 26 次（84%）
- desktop: 4 次（13%）
- other: 1 次（3%）
- **无任何业务场景被识别**（browser/wechat/1688/dingtalk/telegram/jingdong 全为 0）❌

### 4.3 VLM 输出质量
- silent: 25 次（81%）—"没有明显需要处理的内容或异常"
- normal: 6 次（19%）— 检测到登录项通知等
- urgent: 0 次
- **问题**：VLM 回答高度模板化，几乎每次都是相同的"没有异常"句式
- 说明：要么屏幕确实没什么内容（夜间），要么 VLM prompt 不够有引导性

## 5. DRY_RUN=False 可行性评估

### 5.1 6 项前置条件

| # | 条件 | 当前状态 | 评估 |
|---|------|---------|------|
| ① | 业务场景稳定识别 | ❌ 今天 0 个业务场景 | **核心阻塞** |
| ② | wininfo 正确无噪音 | ✅ 仅 browser/wechat 触发 | 通过 |
| ③ | RPA 脚本路径存在 | ✅ 14.5KB，24 个函数 | 通过 |
| ④ | 非 busy hours 不误触发 | ✅ 夜间全部 silent | 通过 |
| ⑤ | 日志跟踪机制成熟 | ✅ dry-run 记录连续增长 | 通过 |
| ⑥ | 回滚方案已测试 | ❌ 无备份文件 | **需补充** |

**结论**：3/6 通过，**DRY_RUN=False 不可行**

### 5.2 阻塞根因分析

**核心问题**：场景分类模型（qwen3-vl:2b）无法在夜间识别业务场景。

原因推测：
1. **数据偏差**：训练/提示词偏向于识别"有内容的屏幕"，夜间屏幕大多空闲
2. **分类粒度不够**：9 类太粗，无法区分 "browser 打开但空白" vs "browser 有网页内容"
3. **屏幕亮度/暗色模式**：夜间用户可能开暗色模式，影响 YOLO 预分类

## 6. DRY_RUN=False 路线图

### Phase 1: 基础稳固（当前）
- [ ] 补充 handler.py.bak 备份
- [ ] 修复暗屏检测（当前逻辑有缺陷）
- [ ] 改进场景分类 prompt（增加业务场景示例）

### Phase 2: 坐标系上线（关键阻塞）
- [ ] 改造 `get_scene_type` 返回 `{scene: "browser", elements: [{text, x, y, w, h}]}`
- [ ] 使用 qwen3-vl 的 bounding box 能力（qwen2.5-vl 原生支持 bbox 输出）
- [ ] handler 接收坐标 → RPA 脚本 `click x,y`

### Phase 3: 多步操作（RPA 扩展）
- [ ] 增加 `drag`、`right_click`、`double_click` 动作
- [ ] 增加 `find_element_by_text` 动作（区域 OCR + 坐标返回）
- [ ] 增加 `wait_for_element` 超时等待

### Phase 4: 意图验证（Microsoft Taxonomy v2.0 映射）
- [ ] auto_execute 前加 intent validation（防 Goal Hijacking）
- [ ] delegate_task subagent 执行日志跟踪（防 Inter-Agent Trust Escalation）
- [ ] SKILL.md loading integrity check

### Phase 5: 上线 DRY_RUN=False
- [ ] 所有前置条件通过 → 逐步放开场景
- [ ] browser/wechat/1688 第一批放开（有明确动作定义）
- [ ] 其他场景第二批放开

## 7. 与 Microsoft Taxonomy v2.0 的映射

| Microsoft 失败模式 | Hermes 映射 | 优先级 |
|---|---|---|
| Goal Hijacking | prompt injection 注入 SKILL.md → 任务重定向 | **HIGH** |
| Inter-Agent Trust Escalation | delegate_task subagent 自汇报不验证 | **HIGH** |
| CUA Visual Attack | screen_watcher 视觉层攻击 | MEDIUM |
| Session Context Contamination | memory/SOUL.md 被污染 | MEDIUM |
| Zero-Click HitL Bypass | DRY_RUN=False 后暴露 | MEDIUM |
