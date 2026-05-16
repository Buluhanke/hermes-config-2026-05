#!/usr/bin/env python3
"""
Hermes vision-agent 视觉全域感知
Phase 2: 长出眼睛

主流程：
See（截屏） -> Think（VLM分析） -> Act（拟真点击）

与 humanization_core 配合：
- capture_screen(): 截屏
- find_element_by_vision(): 找坐标
- vlm_click(): 截图 + 视觉定位 + 拟真点击全流程
- ask_vlm(): 直接问视觉模型问题

典型用法：
    from vision_agent import vlm_click
    vlm_click("加入进货单")
"""

import sys
import os
# 将 humanization-core 目录加入 path
_humanization_dir = os.path.join(os.path.dirname(__file__), '..', 'hermes-humanization-core')
sys.path.insert(0, os.path.abspath(_humanization_dir))

from humanization_core import (
    capture_screen, ask_vlm, human_click, human_move,
    find_element_by_vision, analyze_emotion, SCREENSHOT_PATH,
    human_scroll, human_reading_time, vlm_click,
    ask_vlm_fast, is_human_takeover_active, wait_for_human_release
)

# ─────────────────────────────────────────
# 场景化操作：1688 商品页
# ─────────────────────────────────────────
def search_1688(keyword: str):
    """1688 搜索流程"""
    # 找搜索框
    coords = find_element_by_vision("1688搜索框")
    if not coords:
        print("[vision] 1688: 无法找到搜索框")
        return False
    human_click(*coords)
    import time; time.sleep(0.5)

    # 拟真输入关键词
    from humanization_core import human_type
    human_type(keyword)
    time.sleep(0.3)

    # 找搜索按钮
    vlm_click("搜索按钮")
    print(f"[vision] 1688: 搜索 「{keyword}」 完成")
    return True


def add_1688_to_cart():
    """1688 加入进货单"""
    # 等待页面加载
    import time
    time.sleep(human_reading_time(500))  # 约60秒阅读时间

    result = vlm_click("加入进货单")
    if result:
        print("[vision] 1688: 已加入进货单")
    return result


def view_1688_supplier_details():
    """1688 查看供应商详情"""
    vlm_click("查看联系方式")
    import time; time.sleep(2)
    # 截一张确认
    img = capture_screen()
    result = ask_vlm(img, "供应商联系方式是否可见？简单回答：是或否。")
    return "是" in result


# ─────────────────────────────────────────
# 场景化操作：微信
# ─────────────────────────────────────────
def wechat_send_image(image_path: str, contact_name: str = None):
    """
    通过视觉在微信PC版发送图片
    流程：找微信图标 -> 点击 -> 找联系人 -> 找附件按钮 -> 选图片 -> 发送
    """
    # 1. 点击微信图标（如果桌面有）
    wechat_icon = find_element_by_vision("微信图标")
    if wechat_icon:
        human_click(*wechat_icon)
        import time; time.sleep(2)  # 等微信启动

    # 2. 找联系人
    if contact_name:
        search_coords = find_element_by_vision("微信搜索框")
        if search_coords:
            human_click(*search_coords)
            from humanization_core import human_type
            human_type(contact_name)
            import time; time.sleep(1)
            vlm_click(f"联系人：{contact_name}")

    # 3. 找附件按钮（回形针图标）
    import time
    attach_coords = find_element_by_vision("附件按钮")
    if not attach_coords:
        attach_coords = find_element_by_vision("回形针图标")
    if attach_coords:
        human_click(*attach_coords)
        time.sleep(0.5)

        # 4. 找图片选项
        img_option = find_element_by_vision("图片选项")
        if img_option:
            human_click(*img_option)
            time.sleep(1)

            # 5. 在文件对话框里输入路径
            print(f"[vision] 请手动在文件选择框中选择图片：{image_path}")
            return True

    print("[vision] 微信发送流程中断")
    return False


# ─────────────────────────────────────────
# 场景化操作：桌面全局
# ─────────────────────────────────────────
def find_and_open_app(app_name: str) -> bool:
    """
    视觉找桌面/ Dock 上的应用并打开
    例：find_and_open_app("Safari")
    """
    coords = find_element_by_vision(f"{app_name}图标")
    if coords:
        human_click(*coords)
        import time; time.sleep(2)
        print(f"[vision] 已打开：{app_name}")
        return True
    print(f"[vision] 未找到：{app_name}")
    return False


# ─────────────────────────────────────────
# 通用 VLM 问答（看屏幕回答问题）
# ─────────────────────────────────────────
def ask_screen(question: str) -> str:
    """截一张当前屏幕，问 VLM 问题"""
    img = capture_screen()
    return ask_vlm(img, question)


# ─────────────────────────────────────────
# 自检
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== Hermes vision-agent 自检 ===")

    # 测试截屏
    img = capture_screen()
    print(f"截屏: {img}")

    # 测试屏幕问答
    result = ask_screen("当前屏幕是什么内容？用一句话描述。")
    print(f"屏幕内容: {result[:100]}")

    # 测试找元素
    coords = find_element_by_vision("访达图标")
    print(f"访达图标坐标: {coords}")
