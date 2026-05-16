#!/usr/bin/env python3
"""
Hermes Desktop RPA — 桌面全栈自动化
架构: AppleScript AXUI → 区域截图 → Baidu OCR → cliclick键鼠
用法: python3 hermes_desktop_rpa.py <动作> [参数...]

可用动作:
  ocr           截图+OCR读取屏幕文字
  wininfo       获取Chrome窗口位置/尺寸/标题
  click x,y     点击屏幕坐标
  type <文字>    粘贴文字到当前焦点
  press <键>     按键 (enter/tab/esc/cmd-空格等)
  openurl <URL>  在Chrome打开URL
  send <消息>    在ChatGPT输入并发送
  readchat      读取ChatGPT回复
  scroll <次数>  滚动 (负=向下)

示例:
  python3 hermes_desktop_rpa.py wininfo
  python3 hermes_desktop_rpa.py ocr --region 0,30,1920,960
  python3 hermes_desktop_rpa.py click 960,860
  python3 hermes_desktop_rpa.py type "你好，ChatGPT"
  python3 hermes_desktop_rpa.py send "用中文介绍一下你自己"
  python3 hermes_desktop_rpa.py readchat
"""

import base64, json, os, subprocess, sys, time, re


# ─── 工具函数 ─────────────────────────────────────────────

def run(cmd, timeout=30, shell=False):
    """执行shell命令，返回输出"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=shell)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except FileNotFoundError:
        return "", "命令不存在: " + cmd[0], -1


def ensure_file(content, path="/tmp/_hermes_as.scpt"):
    """写AppleScript文件（避免terminal解析&问题）"""
    with open(path, "w") as f:
        f.write(content)
    return path


def load_env():
    """加载~/.hermes/.env"""
    env = {}
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


# ─── 核心功能 ─────────────────────────────────────────────

def ocr(image_path="/tmp/hermes_screen.png"):
    """Baidu OCR识别图片文字"""
    env = load_env()
    if not all(k in env for k in ["BAIDU_API_KEY", "BAIDU_SECRET_KEY"]):
        return {"error": "缺少BAIDU_API_KEY或BAIDU_SECRET_KEY (.env)"}

    # 获取token
    token_url = (f"https://aip.baidubce.com/oauth/2.0/token"
                 f"?grant_type=client_credentials"
                 f"&client_id={env['BAIDU_API_KEY']}"
                 f"&client_secret={env['BAIDU_SECRET_KEY']}")
    out, err, code = run(["curl", "-s", token_url], timeout=15)
    if code != 0:
        return {"error": f"Token获取失败: {err}"}
    token = json.loads(out).get("access_token", "")
    if not token:
        return {"error": f"Token为空: {out[:200]}"}

    # 读取图片
    if not os.path.exists(image_path):
        return {"error": f"图片不存在: {image_path}"}
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    # OCR调用
    ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={token}"
    out, err, code = run(["curl", "-s", ocr_url,
                          "--data-urlencode", f"image={b64}"], timeout=30)
    if code != 0:
        return {"error": f"OCR失败: {err}"}
    
    result = json.loads(out)
    if "words_result" in result:
        texts = [w["words"] for w in result["words_result"]]
        return {"text": "\n".join(texts), "count": len(texts)}
    else:
        return {"error": json.dumps(result, ensure_ascii=False)[:500]}


def screenshot_region(region=None, output="/tmp/hermes_screen.png"):
    """截图指定区域或全屏"""
    if region:
        x, y, w, h = region
        r = run(["screencapture", "-x", "-R", f"{x},{y},{w},{h}", output], timeout=10)
    else:
        r = run(["screencapture", "-x", output], timeout=10)
    if r[2] == 0:
        return {"path": output, "size": os.path.getsize(output) if os.path.exists(output) else 0}
    return {"error": f"截图失败: {r[1]}"}


def get_chrome_window():
    """AXUI获取Chrome窗口信息"""
    script = '''
tell application "System Events"
    set chromeProc to first process whose name is "Google Chrome"
    set chromeWin to first window of chromeProc
    set winTitle to title of chromeWin
    set {x, y} to position of chromeWin
    set {w, h} to size of chromeWin
    return winTitle & "|" & x & "," & y & "|" & w & "," & h
end tell
'''
    path = ensure_file(script)
    out, err, code = run(["osascript", path], timeout=10)
    if code != 0:
        # 可能Chrome没在跑
        return {"error": f"获取窗口信息失败: {err}"}
    parts = out.split("|")
    if len(parts) == 3:
        title = parts[0]
        pos = parts[1].split(",")
        size = parts[2].split(",")
        return {
            "title": title,
            "x": int(pos[0]), "y": int(pos[1]),
            "width": int(size[0]), "height": int(size[1])
        }
    return {"error": f"解析失败: {out}"}


def chrome_open_url(url):
    """在Chrome当前标签页打开URL"""
    script = f'''
tell application "Google Chrome"
    activate
    open location "{url}"
end tell
'''
    path = ensure_file(script)
    out, err, code = run(["osascript", path], timeout=15)
    return {"success": code == 0, "url": url, "error": err if code != 0 else None}


def chrome_get_url():
    """获取Chrome当前标签页URL"""
    script = '''
tell application "Google Chrome"
    if (count of windows) > 0 then
        return URL of active tab of window 1
    end if
end tell
'''
    path = ensure_file(script)
    out, err, code = run(["osascript", path], timeout=10)
    return {"url": out} if code == 0 else {"error": err}


def click(x, y):
    """用cliclick点击坐标"""
    out, err, code = run(["cliclick", f"c:{x},{y}"], timeout=10)
    return {"x": x, "y": y, "success": code == 0, "error": err if code != 0 else None}


def press_key(key):
    """
    按键 (enter/tab/esc/delete/space等单键名称)
    ⚠️ 不支持组合键格式如 cmd+a / cmd+v —— 
    组合键用 paste_text()，或拆分 kd:cmd + v + ku:cmd
    """
    out, err, code = run(["cliclick", "kp:" + key], timeout=10)
    return {"key": key, "success": code == 0, "error": err if code != 0 else None}


def paste_text(text):
    """通过剪贴板粘贴文字"""
    # pbcopy传入文字
    r1 = subprocess.run(["pbcopy"], input=text.encode(), timeout=5)
    # cmd+v粘贴
    out, err, code = run(["cliclick", "kd:cmd", "v", "ku:cmd"], timeout=5)
    return {"text": text, "success": code == 0 and r1.returncode == 0,
            "error": err if code != 0 else None}


def activate_chrome():
    """激活Chrome窗口到前台"""
    out, err, code = run(["osascript", "-e",
                          'tell application "Google Chrome" to activate'], timeout=5)
    return {"success": code == 0}


def scroll(clicks=-3):
    """滚动鼠标滚轮"""
    out, err, code = run(["cliclick", "kp:arrow-" + ("down" if clicks < 0 else "up")] * abs(clicks),
                         timeout=10)
    return {"clicks": clicks, "success": code == 0}


# ─── 复合操作 ─────────────────────────────────────────────

def chatgpt_send(message):
    """
    在ChatGPT页面输入并发送消息。
    假设ChatGPT已在Chrome前台打开。
    """
    # 1. 获取窗口尺寸
    win = get_chrome_window()
    if "error" in win:
        return {"error": win["error"]}
    
    # 2. 计算输入框坐标（窗口底部居中偏左，因为左侧栏占250px左右）
    input_x = win["x"] + win["width"] // 2 + 50  # 偏右避开侧栏
    input_y = win["y"] + win["height"] - 80       # 底部
    
    # 3. 点击输入框区域
    click(input_x, input_y)
    time.sleep(1)
    
    # 4. 粘贴消息
    paste_text(message)
    time.sleep(0.5)
    
    # 5. 回车发送
    press_key("enter")
    
    return {
        "action": "send",
        "message": message[:80] + ("..." if len(message) > 80 else ""),
        "input_coord": (input_x, input_y),
        "window": win
    }


def chatgpt_read_response(output_path="/tmp/hermes_chat_response.png"):
    """
    截图ChatGPT回复区域+OCR读取内容
    先激活Chrome确保在最前，避免截到其他窗口
    """
    activate_chrome()
    time.sleep(0.5)
    
    win = get_chrome_window()
    if "error" in win:
        return {"error": win["error"]}
    
    # ChatGPT 1920x960布局:
    # 左侧栏: 0~260px (对话历史)
    # 主内容区: 260~1920px 
    # 输入框: 底部 ~80px
    # 顶部: 工具栏 ~60px
    # 回复区域 = 主内容区中间部分
    sidebar_w = 260
    
    content_region = (
        win["x"] + sidebar_w + 20,    # 略过侧栏右边距
        win["y"] + 60,                # 去掉顶部工具栏
        win["width"] - sidebar_w - 40, # 主内容区宽度
        win["height"] - 160            # 去掉输入框
    )
    
    # 截图
    screenshot_region(content_region, output_path)
    
    # OCR
    result = ocr(output_path)
    return result


# ─── CLI入口 ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法: python3 hermes_desktop_rpa.py <动作> [参数...]")
        print("可用动作: ocr, wininfo, click, type, press, openurl, send, readchat, scroll")
        sys.exit(1)

    action = sys.argv[1]
    
    if action == "wininfo":
        result = get_chrome_window()
    
    elif action == "ocr":
        region = None
        output = "/tmp/hermes_screen.png"
        for i, arg in enumerate(sys.argv[2:], 2):
            if arg == "--region" and i+1 < len(sys.argv):
                parts = sys.argv[i+1].split(",")
                region = tuple(int(p) for p in parts)
            elif arg == "--output" and i+1 < len(sys.argv):
                output = sys.argv[i+1]
        if region:
            screenshot_region(region, output)
        else:
            screenshot_region(output=output)
        result = ocr(output)
    
    elif action == "click":
        if len(sys.argv) < 3:
            result = {"error": "需要坐标参数, 如: click 960,860"}
        else:
            parts = sys.argv[2].split(",")
            result = click(int(parts[0]), int(parts[1]))
    
    elif action == "type":
        if len(sys.argv) < 3:
            result = {"error": "需要文字参数"}
        else:
            text = sys.argv[2]
            result = paste_text(text)
    
    elif action == "press":
        if len(sys.argv) < 3:
            result = {"error": "需要按键名, 如: press enter"}
        else:
            result = press_key(sys.argv[2])
    
    elif action == "openurl":
        if len(sys.argv) < 3:
            result = {"error": "需要URL参数"}
        else:
            result = chrome_open_url(sys.argv[2])
    
    elif action == "send":
        if len(sys.argv) < 3:
            result = {"error": "需要消息参数"}
        else:
            result = chatgpt_send(sys.argv[2])
    
    elif action == "readchat":
        result = chatgpt_read_response()
    
    elif action == "scroll":
        clicks = int(sys.argv[2]) if len(sys.argv) > 2 else -3
        result = scroll(clicks)
    
    elif action == "activate":
        result = activate_chrome()
    
    elif action == "url":
        result = chrome_get_url()
    
    else:
        result = {"error": f"未知动作: {action}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
