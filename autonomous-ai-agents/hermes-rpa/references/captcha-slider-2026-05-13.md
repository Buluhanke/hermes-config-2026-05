# Captcha Slider — 滑动条验证码拟人化处理（2026-05-13）

## 核心发现

滑动条验证码检测**不是**轨迹本身，而是：
1. 速度是否恒定（真人忽快忽慢）
2. 有没有"回退校准"（真人会overshoot再微调）
3. 起点有没有随机停顿

## 人类拖拽物理特征

| 阶段 | 速度 | 特征 |
|------|------|------|
| 起点 | 0px/s | 按下前随机停顿50-150ms |
| 初期 | 300-500px/s | 较快 |
| 中段 | 150-300px/s | 正常 |
| 接近终点 | 50-100px/s | 明显减速 |
| overshoot | — | 超过终点5-15px |
| 回退 | 30-50px/s | 慢速回退3-8px |
| 最终微调 | 10-30px/s | 多次小幅度修正 |
| 释放 | — | 按住50-100ms再松开 |

## 核心实现（来自 ~/Vision_Lab/captcha_slider.py）

```python
def _humanoid_path(x1, y1, x2, y2, roughness=1.0):
    """Bezier曲线路径（不走直线）+ 自然抖动"""
    cx1 = x1 + (x2-x1)*0.3 + random.uniform(-30,30)*roughness
    cy1 = y1 + random.uniform(-20,20)*roughness
    cx2 = x1 + (x2-x1)*0.7 + random.uniform(-30,30)*roughness
    cy2 = y2 + random.uniform(-20,20)*roughness
    points = []
    for t in [i/20 for i in range(21)]:
        t1 = 1-t
        x = t1**3*x1 + 3*t1**2*t*cx1 + 3*t1*t**2*cx2 + t**3*x2
        y = t1**3*y1 + 3*t1**2*t*cy1 + 3*t1*t**2*cy2 + t**3*y2
        points.append((x, y))
    return points

def human_drag(start_x, start_y, end_x, end_y, 回退校准=True):
    """拟人化拖拽：变速度 + overshoot回退"""
    time.sleep(random.uniform(0.05, 0.15))  # 起点犹豫
    path = _humanoid_path(start_x, start_y, end_x, end_y, roughness=0.8)
    split = int(len(path) * 0.7)
    for i, (x, y) in enumerate(path):
        delay = random.uniform(0.005, 0.015) if i < split else random.uniform(0.03, 0.08)
        subprocess.run(["cliclick", f"m:{x:.0f},{y:.0f}"])
        time.sleep(delay)
    # overshoot + 回退
    if 回退校准:
        dx = (end_x-start_x)/max(abs(end_x-start_x),1)
        dy = (end_y-start_y)/max(abs(end_y-start_y),1)
        overshoot_px = random.randint(5,15)
        # ... overshoot then backtrack
    subprocess.run(["cliclick", "ku:0"])
```

## 坑

- ❌ Playwright `drag_and_drop`：速度固定，100%被识别
- ❌ 直线移动：必须Bezier曲线
- ❌ 没有overshoot：这是真人最明显特征
- ❌ 停顿太规律：必须`random.uniform`
