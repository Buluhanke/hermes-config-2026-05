"""
Humanization Engine - 拟人化操作模块
生成贝塞尔曲线轨迹、人类打字节奏、行为相关性

导出:
    mouse: generate_human_trajectory, get_speed_factor, set_cognitive_load
    keyboard: type_text
"""

from humanization_engine.mouse import (
    generate_human_trajectory,
    get_speed_factor,
    set_cognitive_load,
    get_cognitive_load,
    Point,
)
from humanization_engine.keyboard import type_text

__all__ = [
    "generate_human_trajectory",
    "get_speed_factor",
    "set_cognitive_load",
    "get_cognitive_load",
    "type_text",
    "Point",
]
