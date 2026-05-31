# Handler 优化：暗屏检测 + 分类降速 + 紧急修复（2026-06-01 实装）

## 动机

2026-06-01 产线数据分析发现：

| 指标 | 值 | 问题 |
|------|-----|------|
| 场景分类耗时 | 35-47s | resize 800px 太高，分类不需要高分辨率 |
| 内容分析耗时 | ~35s | — |
| 完整处理周期 | 70-84s | 远超 watcher 冷却 15s |
| Handler抑制次数 | 302 次/80分钟 | 周期过长导致堆积 |
| 假阳性 [urgent] | 100% unknown/other | qwen3-vl:2b 对空白屏幕幻觉出"异常" |

## 改进项

### 1. 夜间锁屏跳过检测（`is_dark_screenshot()`）

**新增函数**：快速检测截图是否过暗（锁屏/黑屏/屏保）

```python
def is_dark_screenshot(image_path, threshold=25):
    """快速检测截图是否过暗（夜间锁屏/黑屏）"""
    try:
        # 用 sips 生成 10x10 缩略图
        small_tmp = "/tmp/hermes_brightness_check.jpg"
        subprocess.run(["sips", "-z", "10", "10", image_path, "--out", small_tmp],
                       check=True, capture_output=True, timeout=5)
        # 纯色/暗色压缩后体积极小
        with open(small_tmp, "rb") as f:
            data = f.read()
        if len(data) < 500:
            return True
        return False
    except:
        return False
```

**在 `on_trigger()` 中的调用点**：在 `get_scene_type()` 之前调用，跳过 scene classification + ask_screen

**预期收益**：夜间每次触发从 ~80s CPU 降至 ~0.5s（节省 ~98%）

### 2. 场景分类降速

**改动**：`get_scene_type()` 的 resize 从 800px 降至 400px

```python
# 修改前
resize_for_vision(image_path, SCREENSHOT_SMALL)        # 默认 max_w=800

# 修改后
resize_for_vision(image_path, SCREENSHOT_SMALL, max_w=400)
```

- 场景分类（browser/wechat/desktop/other）不需要精细定位
- 预期：35-47s → ~15-20s

### 3. unknown/other 紧急标记修复

**问题**：之前所有场景（含 unknown/other）都经过完整 URGENT_KEYWORDS 检查，qwen3-vl:2b 对空白/锁屏截图幻觉出"异常"/"错误"，所有 [urgent] 均误标

**修复**：unknown/other 仅检查 CRITICAL_KEYWORDS（错误/崩溃/异常/Error/crash），其余全部 silent

```python
if scene_type in ("unknown", "other"):
    CRITICAL_KEYWORDS = ["错误", "崩溃", "闪退", "失败", "异常", "Error", "crash"]
    for kw in CRITICAL_KEYWORDS:
        if kw.lower() in answer_lower:
            urgency = "urgent"
            break
else:
    for kw in URGENT_KEYWORDS:
        if kw.lower() in answer_lower:
            urgency = "urgent"
            break
```

**预期收益**：减少 90%+ 虚假 [urgent] 推送

### 4. COOLDOWN_SECONDS 减半（120 → 60）

Handler 优化后更快 → 60s 冷却足以防止堆积

## 备份

- `~/.hermes/scripts/screen_trigger_handler.py.bak.20260601_0022`
