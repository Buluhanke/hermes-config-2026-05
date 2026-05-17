#!/usr/bin/env python3
"""
1688 滑动验证码闭环
流程：
  检测验证码 → 截图 → VLM识别缺口 → 贝塞尔轨迹拖动 → 验证结果

依赖：
  - humanization_core.human_move, human_click
  - humanization_core.capture_screen, ask_vlm (smolvlm2)
  - 备选：VLM 模型 qwen2.5vl:7b（如果可用）
"""

import sys
import os
import re
import time
import random
import numpy as np
from pathlib import Path

HERMES_SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(HERMES_SKILL_DIR))

from humanization_core import human_move, human_click, capture_screen, ask_vlm, pyautogui


# ─── 验证码检测 ───────────────────────────────────────────

def detect_slider_captcha(img_path: str = None) -> bool:
    """检测页面上是否存在滑动验证码
    通用特征：nc_wrapper / captcha / slider / sliderImg
    """
    if img_path is None:
        img_path = capture_screen()

    prompt = (
        "请判断这张截图里是否有滑动验证码（拼图滑块/滑动验证）。"
        "特征：一个半透明拼图块在图片上，背景有缺失的轮廓。"
        "回复格式：\n"
        "  有验证码: YES\n"
        "  无验证码: NO"
    )

    try:
        response = ask_vlm(img_path, prompt).strip().upper()
        return "YES" in response
    except Exception:
        # 网络或模型问题，降级为 False（不阻断流程）
        return False


# ─── 缺口位置识别 ─────────────────────────────────────────

def find_gap_position(captcha_img_path: str = None) -> int:
    """用 VLM 识别滑动验证码缺口的 x 坐标

    Args:
        captcha_img_path: 验证码背景图路径（不含滑块的那张）
                          如果不传，自动截全屏

    Returns:
        int: 缺口中心的 x 像素坐标

    1688 极验滑块特征：
      - 背景图宽度约 280-300px
      - 滑块宽度约 40-50px
      - 缺口就在滑块正下方/右侧
    """
    if captcha_img_path is None:
        captcha_img_path = capture_screen()

    prompt = (
        "这是1688登录页的滑动验证码截图。\n"
        "请找出拼图缺口的中心 x 坐标（像素）。\n"
        "只看背景图区域（不含右侧拖动滑块）。\n"
        "缺口是背景图中缺失的那块拼图轮廓。\n"
        "只回复一个数字（x坐标），不要任何其他文字。\n"
        "例如：142"
    )

    raw = ask_vlm(captcha_img_path, prompt).strip()
    # 提取纯数字
    numbers = re.findall(r'\d+', raw)
    if not numbers:
        raise ValueError(f"VLM 未返回有效数字，原始回复：{raw}")

    gap_x = int(numbers[0])

    # 边界保护
    gap_x = max(20, min(gap_x, 500))
    return gap_x


# ─── 滑块拖动轨迹生成（二阶贝塞尔 + 随机抖动） ────────────

def generate_slider_track(target_x: int, start_x: int = 50) -> list:
    """生成滑块拖动轨迹（水平移动）

    真人滑块特征：
    - 起步极快（前 30% 路程）
    - 中段略有停顿/抖动
    - 尾部减速贴合

    Args:
        target_x: 目标缺口 x 坐标
        start_x: 滑块初始 x 坐标

    Returns:
        [(x, y), ...] 轨迹点列表
    """
    distance = target_x - start_x
    if distance <= 0:
        return [(start_x, 0)]

    total_steps = random.randint(45, 70)
    track = []

    for i in range(total_steps):
        t = i / total_steps

        # 速度曲线：先快后慢
        if t < 0.3:
            # 快速起步
            speed = 3.5 * (t / 0.3)
        elif t < 0.7:
            # 中段轻微抖动
            speed = 3.5 + random.uniform(-0.5, 1.0)
        else:
            # 尾部减速贴合
            speed = 3.5 * (1 - t) * 2.5
            speed = max(speed, 0.3)

        x = start_x + distance * (i / total_steps)
        # 微小垂直抖动（±2px），模拟人手不稳
        y = random.uniform(-2, 2)
        track.append((int(x), y))

    # 确保最后一帧精确到达
    track[-1] = (target_x, 0)
    return track


# ─── 主流程：滑动通过验证码 ─────────────────────────────────

def solve_slider_captcha(
    slider_handle_x: int,
    slider_handle_y: int,
    gap_x: int,
) -> bool:
    """执行滑动验证

    Args:
        slider_handle_x, slider_handle_y: 滑块把柄中心坐标
        gap_x: 目标缺口 x 坐标

    Returns:
        True = 验证通过，False = 失败
    """
    print(f"[SliderCaptcha] 滑块起始 ({slider_handle_x}, {slider_handle_y}) → 目标缺口 x={gap_x}")

    # 生成轨迹
    track = generate_slider_track(gap_x, start_x=slider_handle_x)
    print(f"[SliderCaptcha] 生成轨迹 {len(track)} 步")

    # 第一步：移动鼠标到滑块上方（不过冲，因为是水平拖动）
    human_move(slider_handle_x, slider_handle_y)

    # 按下鼠标
    pyautogui.mouseDown(button='left')
    time.sleep(random.uniform(0.1, 0.25))

    # 沿轨迹拖动
    for i, (tx, ty) in enumerate(track):
        # 用 pyautogui.dragRel 不走 human_move，直接水平拖动
        # 但我们手动分步拖入，每步之间加随机延迟
        pyautogui.moveTo(tx, slider_handle_y + int(ty), _pause=False)
        step_delay = random.uniform(0.008, 0.02) if i < len(track) - 1 else random.uniform(0.02, 0.05)
        time.sleep(step_delay)

    # 松开鼠标
    pyautogui.mouseUp(button='left')
    print("[SliderCaptcha] 拖动完成，等待验证结果...")

    # 等待验证动画（1-2秒）
    time.sleep(random.uniform(1.5, 2.5))

    # 截图验证是否通过（检查是否有"验证通过"字样）
    result_path = capture_screen()
    prompt = (
        "检查这张截图是否显示滑动验证成功（绿色对勾、\"验证通过\"、"
        "\"验证成功\"等都是成功的标志）。"
        "回复格式：\n"
        "  成功: PASS\n"
        "  失败或还在验证中: FAIL"
    )
    try:
        result = ask_vlm(result_path, prompt).strip().upper()
        success = "PASS" in result
        print(f"[SliderCaptcha] 验证结果：{'✅ 通过' if success else '❌ 失败'}")
        return success
    except Exception as e:
        print(f"[SliderCaptcha] 验证请求失败: {e}，保守返回 False")
        return False


# ─── 懒人入口：自动检测 + 自动找滑块 + 自动拖动 ────────────

def auto_solve_if_present() -> bool:
    """检测当前屏幕是否有验证码，有则自动解。

    自动查找滑块把柄（灰色长条，通常在右侧）
    自动识别缺口位置
    自动拖动

    Returns:
        True = 已处理（无论成功失败），False = 没有验证码
    """
    if not detect_slider_captcha():
        print("[SliderCaptcha] 未检测到滑动验证码，跳过")
        return False

    print("[SliderCaptcha] 检测到验证码，开始自动解题...")

    # 1. 找滑块把柄位置（右侧灰色滑槽内的滑块）
    screen_path = capture_screen()
    prompt = (
        "这是一张1688滑动验证码截图。\n"
        "请找到右侧可拖动的滑块把柄（灰色矩形块）的中心坐标。\n"
        "格式：{\"x\": 数字, \"y\": 数字}\n"
        "只返回这个格式，不要其他文字。"
    )
    raw = ask_vlm(screen_path, prompt).strip()
    numbers = re.findall(r'\d+', raw)
    if len(numbers) < 2:
        print(f"[SliderCaptcha] 无法识别滑块位置，原始回复：{raw}")
        return False

    slider_x = int(numbers[0])
    slider_y = int(numbers[1])

    # 2. 找缺口位置
    try:
        gap_x = find_gap_position(screen_path)
    except ValueError as e:
        print(f"[SliderCaptcha] 缺口识别失败: {e}")
        return False

    # 3. 拖动
    return solve_slider_captcha(slider_x, slider_y, gap_x)


if __name__ == "__main__":
    print("[SliderCaptcha] 模块自检：测试 detect_slider_captcha...")
    result = detect_slider_captcha()
    print(f"检测结果：{'有验证码' if result else '无验证码'}")
