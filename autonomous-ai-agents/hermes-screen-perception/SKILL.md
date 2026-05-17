---
name: hermes-screen-perception
description: Hermes屏幕感知真人化技能 — Qwen2.5VL + pyautogui实现看见→看懂→动手闭环
triggers:
  - 屏幕感知
  - 真人化
  - Dock点击
  - 视觉理解
---

# Hermes 屏幕感知真人化技能

## 核心能力
本地Qwen2.5VL做屏幕语义理解，配合pyautogui精确点击，实现"看见→看懂→动手"闭环。

## 关键文件
- `~/.hermes/scripts/hermes_agent.py` — 主脚本（describe/ask/perceive/click-app/click）
- `~/.hermes/scripts/dock_click.py` — Dock精准点击
- `~/.hermes/scripts/screen_vision.py` — 底层截图+VLM调用
- Ollama模型：`qwen2.5vl:7b`（CPU模式，num_gpu:0避免OOM）

## 核心链路

### 1. 截屏 + VLM理解
```python
import base64, requests
with open(img_path, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()
payload = {
    "model": "qwen2.5vl:7b",
    "prompt": "描述图片内容",
    "images": [img_b64],
    "stream": False,
    "options": {"num_gpu": 0}  # 关键：CPU模式
}
resp = requests.post('http://localhost:11434/api/generate', json=payload, timeout=180)
```

### 2. Dock图标精准点击
```python
# 通过Accessibility API获取Dock图标坐标
script = '''tell application "System Events"
tell process "Dock"
repeat with elem in (get every UI element of list 1)
    if name of elem contains "Chrome" then
        set p to position of elem; set s to size of elem
        return (item 1 of p) & "," & (item 2 of p) & "," & (item 1 of s)
    end if
end repeat
end tell
end tell'''
# 用pyautogui点击中心点
pyautogui.click(cx, cy)
```

### 3. 已知Dock图标位置（屏幕1920×1080）
- Chrome: 中心 (997, 1028)
- Dock图标尺寸：67×83(Chrome) 或 68×84

### 4. 浏览器导航
```python
pyautogui.hotkey('command', 'l')  # 激活地址栏
pyautogui.typewrite('www.taobao.com')
pyautogui.press('return')
```

## 性能
- VLM推理：17-28秒/次（CPU模式，M4 Mac mini 24GB）
- 瓶颈：图片转base64太大，解决方案用sips压缩到800×600再推理

## 当前Gap
1. Web页面内元素（搜索框/按钮）无法点击，需AX坐标或DOM解析
2. 移动端完全空白
3. VLM推理速度慢（目标<3秒）
4. CUA overlay窗口会干扰Dock区域点击，用pyautogui绕过

## 验证命令
```bash
python3 ~/.hermes/scripts/hermes_agent.py perceive "打开Chrome"
python3 ~/.hermes/scripts/hermes_agent.py describe
```

## 今日验证成果（2026-05-17）
- VLM: Qwen2.5VL CPU模式 ✅ 18-28秒/次
- Dock点击: Accessibility API + pyautogui ✅
- 浏览器导航: open -a "Google Chrome" "url" ✅（安全不触发block）
- 键盘输入: pyautogui.hotkey('command', 'l') + typewrite ✅
- 完整链路已验证: 截图→VLM理解→Dock点击→键盘导航→打开网页 ✅

## 当前Gap
1. Web元素精确点击：CDP WS不稳，需可靠方案（备选：AXUI读浏览器DOM）
2. 登录/验证码：100%空白
3. VLM推理速度：17-28秒，目标<3秒
4. 移动端：100%空白
5. MCP Chrome：需Hermes MCP管理重启，不能手动kill
