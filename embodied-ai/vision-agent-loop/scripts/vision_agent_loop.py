#!/usr/bin/env python3
"""Vision Agent Loop — 完整执行脚本模板
用法: python3 vision_agent_loop.py <url> [max_steps]
"""
import subprocess, time, base64, json, urllib.request, sys

VLM_MODEL = 'ahmadwaqar/smolvlm2-agentic-gui:latest'
SCREENSHOT_PATH = '/tmp/agent_screen.png'
SCREENSHOT_THUMB = '/tmp/agent_screen_thumb.png'

def screenshot(compress=True):
    subprocess.run(['screencapture', '-x', SCREENSHOT_PATH], capture_output=True)
    if compress:
        subprocess.run(['sips', '-z', '800', '800', SCREENSHOT_PATH, '--out', SCREENSHOT_THUMB], capture_output=True)

def call_vlm(prompt, img_path, timeout=60):
    with open(img_path, 'rb') as f:
        img = base64.b64encode(f.read()).decode()
    payload = {
        'model': VLM_MODEL,
        'prompt': prompt,
        'images': [img],
        'stream': False
    }
    req = urllib.request.Request(
        'http://localhost:11434/api/generate',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        res = json.loads(r.read())
    return time.time() - t0, res.get('response', '')

def parse_action(response):
    """从VLM输出解析action"""
    import re
    # 匹配 JSON 格式
    m = re.search(r'\{[^}]+\}', response)
    if m:
        try:
            data = json.loads(m.group())
            return data.get('action', 'done'), data.get('reasoning', '')
        except:
            pass
    # 降级：提取click坐标
    coord = re.search(r'click\(?([\d.]+)[,\s]+([\d.]+)\)?', response, re.I)
    if coord:
        return f"click({coord.group(1)}, {coord.group(2)})", "从文本提取坐标"
    if 'done' in response.lower() or '完成' in response:
        return 'done', ''
    return 'continue', ''

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://example.com'
    max_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"=== Vision Agent Loop ===")
    print(f"URL: {url}")
    print(f"VLM: {VLM_MODEL}")
    print()

    # 1. 导航
    subprocess.run(['osascript', '-e',
        f'tell application "Google Chrome" to set URL of active tab of window 1 to "{url}"'],
        capture_output=True)
    time.sleep(2)

    for step in range(max_steps):
        print(f"[Step {step+1}] 截图...")
        screenshot()
        print(f"[Step {step+1}] VLM推理...")
        t, response = call_vlm('描述页面：1)标题 2)主要元素 3)下一步建议动作', SCREENSHOT_THUMB)
        print(f"  耗时: {t:.1f}s")
        print(f"  输出: {response[:300]}")
        action, reasoning = parse_action(response)
        print(f"  解析: action={action}, reasoning={reasoning[:80]}")
        if action == 'done':
            print("完成")
            break
        time.sleep(1)

if __name__ == '__main__':
    main()