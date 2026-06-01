# Direction D 执行层巡检 — R6 生产验证 (2026-06-01 07:46)

## 巡检结论

产线全链路正常。YOLO ScreenParser 预分类已大规模验证通过。

## YOLO 预分类生产数据（07:03-07:46，~43分钟）

| 指标 | 值 |
|------|----|
| 总触发次数 | 82 |
| idle 跳过 YOLO | 41 (50.0%) |
| 非 idle 升级 VLM | 41 (50.0%) |
| YOLO 推理时间 | ~93ms @ 320px |
| VLM 场景分类 | ~3s (qwen3-vl:2b, 400px, num_ctx=1024) |
| idle 场景缩短 | 93ms vs ~7s = **75x 加速** |
| 空闲场景正确标记 [silent] | 41/41 (100%) |

**结论**：双层分类器架构（Layer 1 YOLO 93ms → Layer 2 VLM 3s）已稳定产线运行。idle 场景 50% 跳过率，无假阴性。

## 动作多样性（auto_execute）

| 动作 | 使用次数 | 占比 |
|------|---------|------|
| `none` | 230 (June 1 02:50 后) | 61.7% |
| `wininfo` | 143 (含 03:00 前历史) | 38.3% |
| RPA 动作可用 | 11种 | 利用率 2/11 (18.2%) |

**瓶颈**：RPA 支持 click/press_key/paste_text/scroll/ocr/chrome_open_url 等 9 种从未在 auto_execute 中使用。WHITELIST 只有语义分离（idle vs business），无差异化动作。

## 坐标映射链 ✅ 已确认

`hermes_desktop_rpa.py` line 207 `normalized_click(nx, ny)`:
```python
def normalized_click(nx, ny, screen_w=None, screen_h=None):
    """Qwen3-VL 官方公式: x_px = round(coord / 1000 * screen_dim)"""
    x = round(nx / 1000 * screen_w)
    y = round(ny / 1000 * screen_h)
```

与 Qwen3-VL cookbook 的 1000×1000 相对坐标系一致。**不是 /999**。

## DRY_RUN=False 过渡条件

| # | 条件 | 状态 |
|---|------|------|
| ① 基线数据 (≥500) | 967 ✅ | 充足 |
| ② Ollama 稳定性 (unknown < 10%) | 0.54% ✅ | 优秀 |
| ③ 动作多样性 (≥3 种) | 2 种 ❌ | 仅 none + wininfo |
| ④ 坐标映射链 | 已确认 ✅ | normalized_click 正确 |
| ⑤ SafeGround 置信度 | ❌ | 未实现 |
| ⑥ 动作分级 | ❌ | 仅 none/wininfo 两级 |
| **总计** | **3/6 ✅** | 推进③⑤⑥ |

## Gateway 污染

| 指标 | 值 |
|------|----|
| 当前 count | 1957 |
| 增长率 | ~0.2/hr（噪音级） |
| 阈值预警 | 5000+ 时再处理 |

## 产线健康快照

| 指标 | 值 |
|------|----|
| unknown 率（June 1 当日） | 0.54% (2/373) |
| dry-run 总量 | 967 |
| YOLO 预分类 | ✅ 上线运行 |
| handler lock | 无残留 |
| Ollama 进程 | PID 98043 |
| screen_watcher 进程 | PID 48245 |
| 截图新鲜度 | 持续更新（07:45） |
