#!/usr/bin/env python3
"""
PyAutoGUI 桌面控制器 — 鼠标、键盘、截图识别
适用于浏览器外的操作：打开应用、文件对话框、系统设置等

用法: python3 desktop_controller.py <action> [args...]
"""

import pyautogui
import time, json, sys, subprocess

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


def click(x, y, button='left', clicks=1):
    """点击屏幕坐标"""
    pyautogui.click(x, y, clicks=clicks, button=button)
    return {'x': x, 'y': y, 'action': 'click'}


def type_text(text, interval=0.05):
    """输入文本"""
    pyautogui.write(text, interval=interval)
    return {'text_len': len(text)}


def press_key(key):
    """按键盘按键，如 'enter', 'tab', 'esc'"""
    pyautogui.press(key)
    return {'key': key}


def hotkey(*keys):
    """组合键，如 hotkey('command', 'c')"""
    pyautogui.hotkey(*keys)
    return {'keys': keys}


def screenshot(path='/tmp/hermes_desktop.png', region=None):
    """截取全屏或指定区域"""
    img = pyautogui.screenshot(path, region=region)
    return {'path': path, 'size': img.size}


def locate_image(image_path, confidence=0.8):
    """在屏幕上查找图片位置"""
    result = pyautogui.locateOnScreen(image_path, confidence=confidence)
    if result:
        center = pyautogui.center(result)
        return {'found': True, 'left': result.left, 'top': result.top,
                'width': result.width, 'height': result.height,
                'center_x': int(center.x), 'center_y': int(center.y)}
    return {'found': False}


def drag(start_x, start_y, end_x, end_y, duration=0.5):
    """拖拽"""
    pyautogui.moveTo(start_x, start_y)
    pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
    return {'from': (start_x, start_y), 'to': (end_x, end_y)}


def scroll(clicks= -3):
    """滚动鼠标滚轮"""
    pyautogui.scroll(clicks)
    return {'clicks': clicks}


def move_to(x, y, duration=0.3):
    """移动鼠标到指定位置"""
    pyautogui.moveTo(x, y, duration=duration)
    return {'x': x, 'y': y}


def screen_size():
    """返回屏幕尺寸"""
    w, h = pyautogui.size()
    return {'width': w, 'height': h}


def get_position():
    """返回当前鼠标位置"""
    x, y = pyautogui.position()
    return {'x': x, 'y': y}


def open_app(app_name):
    """用 Spotlight 打开应用"""
    pyautogui.hotkey('command', 'space')
    time.sleep(0.5)
    pyautogui.write(app_name, interval=0.05)
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2)
    return {'app': app_name}


def get_active_window_title():
    """获取当前活动窗口标题 (macOS)"""
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.stdout.strip()


# --- CLI 入口 ---
if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'screen_size'
    func = globals().get(action)
    if not func:
        print(json.dumps({'error': f'未知操作: {action}'}))
        sys.exit(1)

    args = sys.argv[2:]
    try:
        # 智能解析参数：数字转int，JSON对象转dict
        parsed = []
        for a in args:
            try:
                parsed.append(int(a))
            except ValueError:
                try:
                    parsed.append(json.loads(a))
                except:
                    parsed.append(a)
        result = func(*parsed)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        sys.exit(1)
