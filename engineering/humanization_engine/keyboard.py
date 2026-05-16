"""
拟人化键盘输入引擎
模拟：停顿、误触、修正、速度变化
与mouse.py共享cognitive_load状态
"""

import random
import time
from typing import Callable, Optional


def _get_nearby_char(char: str) -> str:
    """获取键盘上相近的字符（模拟误触）"""
    nearby = {
        'a': 's', 's': 'd', 'd': 'f', 'f': 'g', 'g': 'h',
        'q': 'w', 'w': 'e', 'e': 'r', 'r': 't', 't': 'y',
        'z': 'x', 'x': 'c', 'c': 'v', 'v': 'b',
        '1': '2', '2': '3', '3': '4', '4': '5',
        '0': '9', '9': '8',
    }
    return nearby.get(char.lower(), char)


def _base_delay_ms(wpm: int) -> float:
    """基准每字符延迟（毫秒）"""
    return 60000 / (wpm * 5)


def type_text(
    send_fn: Callable[[str], None],
    text: str,
    base_wpm: int = 55,
    mistake_rate: float = 0.02,
    use_backspace: bool = True,
    cognitive_load: Optional[float] = None,
) -> int:
    """
    拟人化打字

    参数:
        send_fn: 实际发送字符的函数
        text: 要输入的文本
        base_wpm: 基准速度（单词/分钟）
        mistake_rate: 误触概率
        use_backspace: 是否用退格修正
        cognitive_load: 认知负荷（None则从mouse模块读取）

    返回:
        修正次数
    """
    if cognitive_load is None:
        try:
            from humanization_engine.mouse import get_cognitive_load
            cognitive_load = get_cognitive_load()
        except ImportError:
            cognitive_load = 1.0

    base_delay = _base_delay_ms(base_wpm) / 1000  # 转秒
    corrections = 0

    for i, char in enumerate(text):
        # 速度波动
        progress = i / max(1, len(text) - 1)
        speed_var = random.uniform(0.5, 1.8) * cognitive_load

        # 特殊位置停顿
        if char in '.,!?;:':
            wait = base_delay * speed_var * 2.5
        elif char == ' ':
            wait = base_delay * speed_var * 0.6
        elif i > 0 and i % random.randint(6, 14) == 0:
            # 思考停顿
            wait = base_delay * speed_var * 2.0
        else:
            wait = base_delay * speed_var

        # 误触
        if random.random() < mistake_rate:
            wrong = _get_nearby_char(char)
            send_fn(wrong)
            time.sleep(random.uniform(0.06, 0.2))

            if use_backspace:
                send_fn('\b')
                time.sleep(random.uniform(0.04, 0.1))
                corrections += 1

        send_fn(char)
        time.sleep(max(0.003, wait))

    return corrections
