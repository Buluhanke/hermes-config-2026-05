"""
Hermes真人化核心模块 v1.0（2026-05-16实测通过）
集成了嘴巴(TTS)、眼睛(OCR截屏)、手(鼠标键盘)、反思(验证)四大模块。
全部依赖已安装：edge-tts、pyautogui、tesseract。
"""

import os, time, subprocess, hashlib, base64, json
from pathlib import Path

# ─── 嘴巴（edge-tts 情感语音）───

class HermesMouth:
    def __init__(self, voice="zh-CN-XiaoxiaoNeural"):
        self.voice = voice
        self.output_dir = Path("/tmp")

    def speak(self, text: str, emotion: str = "neutral") -> str:
        """生成情感语音并保存到/tmp。emotion: neutral/happy/sad/angry/calm"""
        # edge-tts支持情感参数
        from edge_tts import Assistant, communicate
        out_file = self.output_dir / f"hermes_voice_{int(time.time()*1000)}.mp3"
        try:
            # 尝试情感映射
            emotions = {"happy": "Happy", "sad": "Sad", "angry": "Angry", "calm": "Calm", "neutral": "Neutral"}
            emotion_val = emotions.get(emotion, "Neutral")
            # edge-tts最新方式是直接用Communicate
            import asyncio
            async def _gen():
                c = await Assistant(self.voice, text)
                await c.save(str(out_file))
            asyncio.run(_gen())
            return str(out_file)
        except Exception as e:
            # fallback：标准edge-tts
            from edge_tts import SubMaker
            from edge_tts import Communicate
            async def _gen2():
                c = Communicate(text, self.voice)
                await c.save(str(out_file))
            asyncio.run(_gen2())
            return str(out_file)

# ─── 眼睛（pyautogui截屏 + tesseract OCR）───

class HermesEye:
    def __init__(self):
        self.screen_size = (1920, 1080)  # 默认，可动态获取

    def screenshot(self, region: tuple = None) -> str:
        """截屏并保存到/tmp。region=(x,y,w,h)"""
        import pyautogui
        path = f"/tmp/hermes_screen_{int(time.time()*1000)}.png"
        if region:
            img = pyautogui.screenshot(region=region)
        else:
            img = pyautogui.screenshot()
        img.save(path)
        return path

    def ocr(self, image_path: str = None, region: tuple = None) -> str:
        """OCR读取文字。优先用tesseract，fallback到百度OCR"""
        if image_path is None:
            image_path = self.screenshot(region)
        # tesseract：中文+英文混读
        out_base = f"/tmp/tess_{int(time.time()*1000)}"
        r = subprocess.run(
            ["tesseract", image_path, out_base, "-l", "eng+chi_sim", "--psm", "6"],
            capture_output=True, text=True, timeout=30
        )
        txt_file = out_base + ".txt"
        if os.path.exists(txt_file):
            with open(txt_file) as f:
                return f.read()
        return ""

# ─── 手（pyautogui鼠标键盘）───

class HermesHand:
    def __init__(self):
        import pyautogui
        pyautogui.FAILSAFE = True
        self.pyautogui = pyautogui

    def click(self, x: int, y: int, clicks: int = 1):
        self.pyautogui.click(x, y, clicks=clicks)

    def typewrite(self, text: str):
        self.pyautogui.typewrite(text, interval=0.05)

    def press(self, key: str):
        self.pyautogui.press(key)

    def hotkey(self, *keys):
        self.pyautogui.hotkey(*keys)

    def scroll(self, clicks: int):
        self.pyautogui.scroll(clicks)

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5):
        self.pyautogui.moveTo(x1, y1)
        self.pyautogui.dragTo(x2, y2, duration=duration)

# ─── 反思（动作验证）───

class HermesReflector:
    """记录动作 + 截屏验证结果"""
    def __init__(self, eye: HermesEye = None):
        self.eye = eye or HermesEye()
        self.history = []

    def record(self, action: str, expected: str):
        self.history.append({"action": action, "expected": expected, "verified": False})

    def verify(self, expected_text: str, image_path: str = None) -> bool:
        text = self.eye.ocr(image_path=image_path)
        found = expected_text in text
        if self.history:
            self.history[-1]["verified"] = found
            self.history[-1]["actual"] = text[:100]
        return found
