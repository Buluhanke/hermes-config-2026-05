"""
拟人化鼠标轨迹引擎
实现：贝塞尔曲线、减速阶段、overshoot、人味速度
"""

import random
import time
from typing import List, Tuple, Callable

Point = Tuple[float, float]


def quadratic_bezier(p0: Point, p1: Point, p2: Point, num_points: int = 50) -> List[Point]:
    """二次贝塞尔曲线"""
    pts = []
    for i in range(num_points):
        t = i / (num_points - 1)
        x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
        y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
        pts.append((x, y))
    return pts


def cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point, num_points: int = 60) -> List[Point]:
    """三次贝塞尔曲线"""
    pts = []
    for i in range(num_points):
        t = i / (num_points - 1)
        x = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t**2*p2[0] + t**3*p3[0]
        y = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t**2*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


def generate_control_points(start: Point, end: Point) -> Tuple[Point, Point, Point, Point]:
    """生成带随机偏移的控制点"""
    dx = end[0] - start[0]
    dy = end[1] - start[1]

    # 控制点1：起点往后延伸
    ctrl1 = (
        start[0] + dx * 0.25 + random.gauss(0, 35),
        start[1] + dy * 0.25 + random.gauss(0, 25)
    )
    # 控制点2：终点往前延伸
    ctrl2 = (
        start[0] + dx * 0.75 + random.gauss(0, 35),
        start[1] + dy * 0.75 + random.gauss(0, 25)
    )
    return start, ctrl1, ctrl2, end


def add_overshoot(base_points: List[Point], end: Point) -> List[Point]:
    """
    添加过头效果：目标点外晃一下再回来
    概率40%，幅度gauss(8±4, 5±3)
    """
    if random.random() > 0.4:
        return base_points

    overshoot_offset = (
        random.gauss(8, 4),
        random.gauss(5, 3)
    )
    overshoot_end = (end[0] + overshoot_offset[0], end[1] + overshoot_offset[1])

    # 出去
    out_curve = quadratic_bezier(end, end, overshoot_end, num_points=12)
    # 回来
    back_curve = quadratic_bezier(overshoot_end, overshoot_end, end, num_points=8)

    base_points.extend(out_curve)
    base_points.extend(back_curve)
    return base_points


def add_slowdown_phase(points: List[Point], end: Point, slowdown_px: int = 15) -> List[Point]:
    """
    终点前减速阶段：最后一段用密集的点模拟减速
    原有速度系数从1.0降到0.2
    """
    if len(points) < 20:
        return points

    # 取最后20个点
    last_section = points[-20:]
    original_end = points[-(len(points) - 20)]

    # 用更密的点重放最后这段（原地踏步效果）
    dense_section = []
    for pt in last_section:
        # 每个点重复2-3次，模拟减速
        repeats = random.randint(2, 3)
        for _ in range(repeats):
            # 加微量抖动
            jitter = (random.gauss(0, 0.5), random.gauss(0, 0.5))
            dense_section.append((pt[0] + jitter[0], pt[1] + jitter[1]))

    # 替换最后20个点为密集版本
    result = points[:-(len(points) - 20)] + dense_section
    return result


def generate_human_trajectory(
    start: Point,
    end: Point,
    cognitive_load: float = 1.0,
) -> List[Point]:
    """
    生成完整的人类鼠标轨迹

    参数:
        start: 起始坐标 (x, y)
        end: 目标坐标 (x, y)
        cognitive_load: 认知负荷系数 (0.5=专注, 1.0=正常, 2.0=分心)
                        影响轨迹的弯曲程度和速度
    """
    # 距离越远，曲线越夸张
    distance = ((end[0] - start[0])**2 + (end[1] - start[1])**2) ** 0.5
    num_points = max(30, min(80, int(distance * 0.4)))

    # 认知负荷高时曲线更不规则
    p0, ctrl1, ctrl2, p3 = generate_control_points(start, end)
    if cognitive_load > 1.2:
        # 分心时控制点偏移更大
        ctrl1 = (ctrl1[0] + random.gauss(0, 20), ctrl1[1] + random.gauss(0, 15))
        ctrl2 = (ctrl2[0] + random.gauss(0, 20), ctrl2[1] + random.gauss(0, 15))

    points = cubic_bezier(p0, ctrl1, ctrl2, p3, num_points=num_points)
    points = add_overshoot(points, end)
    points = add_slowdown_phase(points, end)

    return points


def get_speed_factor(progress: float, cognitive_load: float = 1.0) -> float:
    """
    根据轨迹进度返回速度系数
    progress: 0.0~1.0
    返回: 延迟乘数（越大越慢）
    """
    base = 0.008 * cognitive_load

    if progress < 0.15:
        # 起步慢
        factor = random.uniform(2.5, 4.0)
    elif progress < 0.3:
        # 加速
        factor = random.uniform(0.8, 1.4)
    elif progress > 0.85:
        # 终点前减速
        slowdown = (progress - 0.85) / 0.15  # 0~1
        factor = 0.8 + slowdown * random.uniform(1.5, 2.5)
    else:
        factor = random.uniform(0.7, 1.3)

    return factor


# 全局认知负荷状态（供keyboard模块同步使用）
_cognitive_load = 1.0


def set_cognitive_load(load: float):
    """设置全局认知负荷（0.5~2.0）"""
    global _cognitive_load
    _cognitive_load = max(0.5, min(2.0, load))


def get_cognitive_load() -> float:
    return _cognitive_load
