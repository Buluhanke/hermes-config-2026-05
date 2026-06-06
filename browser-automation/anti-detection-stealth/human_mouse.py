#!/usr/bin/env python3
"""
~/.hermes/skills/browser-automation/anti-detection-stealth/human_mouse.py
拟人化鼠标 — 贝塞尔曲线 + 高斯停顿 + 过冲回调
撞 bot.sannysoft / Cloudflare 行为检测核心

设计原理:
  真人鼠标 = 两段贝塞尔曲线 + 过冲点 + ease-out 速度
  真人停顿时长 = N(μ=80ms, σ=20ms) 截断正态
  真人点击 = mouseDown → 12ms 内可能偏移 0-2px → mouseUp

使用:
  from human_mouse import human_click, human_move
  human_click(ws, x=500, y=300, jitter=0.5)  # jitter 0-1
"""
import math
import random
import time


def _gauss(mu=80.0, sigma=20.0, min_v=20, max_v=300):
    """高斯分布的停顿时长 (截断)"""
    v = random.gauss(mu, sigma)
    return max(min_v, min(max_v, v))


def _bezier_path(x0, y0, x1, y1, overshoot=False):
    """
    生成两段贝塞尔曲线的点序列
    返回: [(x, y, dt_ms), ...]
    """
    # 距离决定总时长
    dist = math.hypot(x1 - x0, y1 - y0)
    # 真人 1000px 约 600-900ms, 加 speed_factor 调节
    duration = max(150, min(900, dist * 0.8 + random.gauss(0, 40)))
    steps = max(15, min(60, int(dist / 12)))

    # 控制点: 起点出发方向 + 终点进入方向 + 中段一个弧
    # 路径偏转强度: 距离越远, 中间弧越大
    arc_strength = min(dist * 0.25, 80) * random.uniform(0.4, 1.2)
    # 中间控制点偏移方向: 垂直于起终点连线, 随机方向
    mid_x = (x0 + x1) / 2
    mid_y = (y0 + y1) / 2
    dx = x1 - x0
    dy = y1 - y0
    # 单位垂直向量
    if dist > 0:
        px = -dy / dist
        py = dx / dist
    else:
        px, py = 0, 0
    # 控制点: 中点 + 垂直偏移
    c1_x = x0 + dx * 0.25 + px * arc_strength
    c1_y = y0 + dy * 0.25 + py * arc_strength
    c2_x = x0 + dx * 0.75 + px * arc_strength * 0.6
    c2_y = y0 + dy * 0.75 + py * arc_strength * 0.6

    # 过冲点 (40% 概率): 终点后再延伸一点
    if overshoot and dist > 50:
        overshoot_amount = random.uniform(3, 12)
        ox = x1 + (dx / dist) * overshoot_amount
        oy = y1 + (dy / dist) * overshoot_amount
    else:
        ox, oy = x1, y1

    # 生成主路径点 (三阶贝塞尔) — ease-out
    points = []
    for i in range(steps + 1):
        t = i / steps
        # ease-out: t^0.5 让开头快, 结尾慢 (像真人快接近时减速)
        t_ease = 1 - (1 - t) ** 2
        # 三阶贝塞尔
        x = (1-t_ease)**3 * x0 + 3*(1-t_ease)**2*t_ease*c1_x + 3*(1-t_ease)*t_ease**2*c2_x + t_ease**3 * ox
        y = (1-t_ease)**3 * y0 + 3*(1-t_ease)**2*t_ease*c1_y + 3*(1-t_ease)*t_ease**2*c2_y + t_ease**3 * oy
        # 时间戳: 总时长按步数均分
        dt = (duration / steps) * (1.0 if i == 0 else 1.0)  # 每步相对上一步
        # 不均匀步长: 头部快尾部慢
        if i > 0:
            prev_t = (i-1) / steps
            prev_t_ease = 1 - (1 - prev_t) ** 2
            # 用 t_ease 的差分来分配时间
            cumulative_t = (3 * t_ease**2 * (1-t_ease) + 3 * t_ease * (1-t_ease)**2 + t_ease**3)
            prev_cumulative = (3 * prev_t_ease**2 * (1-prev_t_ease) + 3 * prev_t_ease * (1-prev_t_ease)**2 + prev_t_ease**3)
            dt = (cumulative_t - prev_cumulative) * duration
        points.append((x, y, max(2, dt)))

    # 如果有过冲, 加一个回退到精确终点的弧
    if overshoot and (ox, oy) != (x1, y1):
        return_back_steps = random.randint(4, 8)
        for i in range(1, return_back_steps + 1):
            t = i / return_back_steps
            # ease-in-out 回退
            t_ease = t * t * (3 - 2 * t)
            x = ox + (x1 - ox) * t_ease
            y = oy + (y1 - oy) * t_ease
            dt = duration * 0.08  # 回退占总时长 8%
            points.append((x, y, dt))

    return points


def _send_mouse_event(ws, msg_id, x, y, button='left', event_type='mouseMoved'):
    """发单个 mouseMoved/mousePressed/mouseReleased 事件"""
    import json
    params = {
        "type": event_type,
        "x": x,
        "y": y,
        "button": button,
        "buttons": 1 if event_type == "mousePressed" else 0,
        "clickCount": 1 if event_type == "mousePressed" else 0,
    }
    ws.send(json.dumps({"id": msg_id, "method": "Input.dispatchMouseEvent", "params": params}))


def human_move(ws, x0, y0, x1, y1, overshoot_prob=0.4):
    """
    拟人化鼠标移动 (从 x0,y0 到 x1,y1)
    overshoot_prob: 过冲概率 (0-1, 真人约 40%)
    """
    overshoot = random.random() < overshoot_prob
    points = _bezier_path(x0, y0, x1, y1, overshoot=overshoot)
    msg_id = [1000]
    last_t = 0
    for x, y, dt in points:
        # 实时 dt
        time.sleep(dt / 1000.0)
        msg_id[0] += 1
        _send_mouse_event(ws, msg_id[0], x, y, event_type='mouseMoved')


def human_click(ws, x, y, current_x=0, current_y=0, jitter=0.5, button='left'):
    """
    拟人化点击: 移动 → 停顿 → 按下 → 抖动 → 抬起
    jitter: 0=精准 1=很飘
    """
    # 1. 移动到目标 (可能有过冲)
    human_move(ws, current_x, current_y, x, y, overshoot_prob=0.4 * jitter)

    # 2. 到达后停顿 (高斯分布, 模仿"看 + 决策"时间)
    pause = _gauss(mu=80 + jitter * 40, sigma=20 + jitter * 10)
    time.sleep(pause / 1000.0)

    # 3. 按下前, 鼠标可能微动 (真人瞄准)
    if jitter > 0.2:
        micro_dx = random.gauss(0, 0.8 * jitter)
        micro_dy = random.gauss(0, 0.8 * jitter)
        import json
        ws.send(json.dumps({"id": 9999, "method": "Input.dispatchMouseEvent",
                            "params": {"type": "mouseMoved", "x": x + micro_dx, "y": y + micro_dy,
                                       "button": "none", "buttons": 0}}))
        time.sleep(random.uniform(0.005, 0.020))

    # 4. 按下
    import json
    ws.send(json.dumps({"id": 9998, "method": "Input.dispatchMouseEvent",
                        "params": {"type": "mousePressed", "x": x, "y": y,
                                   "button": button, "buttons": 1, "clickCount": 1}}))
    # 5. 按下到抬起的间隔 (真人 60-150ms)
    time.sleep(_gauss(mu=85, sigma=25, min_v=40, max_v=180) / 1000.0)

    # 6. 抬起
    ws.send(json.dumps({"id": 9997, "method": "Input.dispatchMouseEvent",
                        "params": {"type": "mouseReleased", "x": x, "y": y,
                                   "button": button, "buttons": 0, "clickCount": 1}}))


def human_double_click(ws, x, y, current_x=0, current_y=0, jitter=0.5):
    """拟人化双击"""
    human_click(ws, x, y, current_x, current_y, jitter)
    # 双击间隔 50-150ms
    time.sleep(_gauss(mu=90, sigma=30, min_v=40, max_v=200) / 1000.0)
    human_click(ws, x, y, x, y, jitter)  # 第二次位置基本不变


# CLI 调试模式: 显示生成的轨迹
if __name__ == "__main__":
    print("=" * 60)
    print("human_mouse.py — 拟人化鼠标轨迹测试")
    print("=" * 60)
    for trial in range(3):
        path = _bezier_path(0, 0, 500, 300, overshoot=True)
        total_dt = sum(p[2] for p in path)
        print(f"\n[轨迹 {trial+1}] 点数={len(path)}, 总时长={total_dt:.0f}ms")
        # 打印关键点
        for i, (x, y, dt) in enumerate(path):
            if i % 5 == 0 or i == len(path) - 1:
                print(f"  [{i:3d}] x={x:6.1f} y={y:6.1f}  dt={dt:5.1f}ms")
        # ASCII 可视化
        print("  轨迹:")
        max_y = 300
        for i in range(0, len(path), max(1, len(path) // 20)):
            x, y, _ = path[i]
            row = int(y / max_y * 10)
            col = int(x / 500 * 40)
            line = [' '] * 42
            line[col] = '●'
            print(f"    {' ' * 0}{''.join(line)}")
        # 停顿分析
        gaps = [path[i+1][2] for i in range(len(path)-1)]
        if gaps:
            avg = sum(gaps) / len(gaps)
            var = sum((g - avg) ** 2 for g in gaps) / len(gaps)
            std = var ** 0.5
            print(f"  步长: avg={avg:.1f}ms std={std:.1f}ms (真人 std/avg ≈ 0.3-0.5)")
