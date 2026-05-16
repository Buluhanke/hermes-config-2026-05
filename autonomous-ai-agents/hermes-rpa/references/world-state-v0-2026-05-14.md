# WorldState v0 实现笔记（2026-05-14）

## 核心文件

`/Users/aimac/hermes-v3/world_state_v0.py`

这是 Phase 1 的最小闭环实现，源自用户提出的路线建议：
> "只做三件事：截图、OCR + bbox、action + before/after diff"

## 架构

```
capture_state()
    │
    ├── screencapture 截图（路径不能用 /tmp/，用 ~/hermes-v3/）
    ├── tesseract OCR（本地离线，优先）
    │   └── 备选：百度 OCR（token权限问题暂不可用）
    ├── UIObject 构建（text/bbox/clickable启发式判断）
    └── WorldState 返回

step() = capture_state() → execute_action() → capture_state() → detect_change()
```

## 关键设计决策

### 1. OCR 引擎选择

| 引擎 | 优点 | 缺点 |
|------|------|------|
| tesseract（本地）| 离线、无限额、稳定 | 精度一般、无精确bbox |
| Baidu OCR（在线）| 精度高、精确bbox | 权限问题、额度限制 |

当前实现优先 tesseract，降级 Baidu OCR。

### 2. tesseract 路径问题

**问题**：沙盒环境（execute_code / terminal）下 tesseract 无法读取 `/tmp/` 目录。
**解决**：截图和 tesseract 输出全部放在项目目录 `~/hermes-v3/` 下。

### 3. clickable 启发式判断

```python
clickable = (len(text) < 40 and
             not any(p in text for p in '，。、；：？！""''（）【】'))
```
短文本且无标点符号 → 可点击按钮。

### 4. Diff 系统

用 `screen_hash`（md5）快速判断屏幕是否变化，再对比文本集合的 diff_ratio。

## 当前状态（2026-05-14）

- ✅ 闭环跑通：capture_state() → 48个UI对象 → 34个可点击
- ✅ 截图 + tesseract OCR 成功
- ⚠️ Baidu OCR token 权限不足（error_code: 3 "Unsupported openapi method"）
- ⚠️ tesseract bbox 不精确（y轴按行估算，非真实坐标）
- ❌ 尚未完成真实点击验证循环

## 下一步（Phase 2 方向）

1. **接 CDP** → 精确 AX Tree 坐标替代 OCR bbox
2. **接 open-webui** → 本地 VL 模型做截图理解（更准的 text）
3. **真实 demo**：在 Chrome 里找到"搜索"按钮并点击，验证 before/after diff
