#!/usr/bin/env python3
"""
Hermes 真人化技能 - 嘴巴+眼睛+手+反思
全部免费，本地优先
"""
import asyncio
import base64
import io
import json
import os
import subprocess
import tempfile
import time
import pyautogui


class HermesMouth:
    """有情感的TTS，edge-tts驱动"""
    def __init__(self, voice='zh-CN-XiaoxiaoNeural'):
        self.voice = voice
        self._available = None
        self._check()

    def _check(self):
        try:
            import edge_tts
            self._available = True
        except:
            self._available = False

    @property
    def available(self):
        return self._available

    async def _speak(self, text, output_path=None, speed=0, pitch=0):
        import edge_tts
        if output_path is None:
            output_path = f"/tmp/hermes_voice_{int(time.time())}.mp3"
        ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2006/10/tts' xml:lang='zh-CN'>
            <prosody rate='{speed}%' pitch='{pitch}Hz'>{text}</prosody>
        </speak>"""
        await edge_tts.Communicate(ssml, self.voice).save(output_path)
        return output_path

    def speak_sync(self, text, speed=0, pitch=0):
        loop = asyncio.new_event_loop()
        path = loop.run_until_complete(self._speak(text, speed=speed, pitch=pitch))
        return path

    def speak(self, text, emotion="neutral"):
        speed_map = {"happy": 10, "sad": -15, "excited": 15, "calm": -5, "angry": 5, "neutral": 0}
        pitch_map = {"happy": 10, "sad": -20, "excited": 20, "calm": -5, "angry": 30, "neutral": 0}
        return self.speak_sync(text, speed=speed_map.get(emotion, 0), pitch=pitch_map.get(emotion, 0))


class HermesEye:
    """macOS屏幕感知"""
    def __init__(self):
        self._tesseract = self._check_tesseract()

    def _check_tesseract(self):
        try:
            subprocess.run(['tesseract', '--version'], capture_output=True, timeout=5)
            return True
        except:
            return False

    @property
    def available(self):
        return True

    @property
    def has_ocr(self):
        return self._tesseract

    def screenshot(self, region=None):
        try:
            if region:
                x, y, w, h = region
                return pyautogui.screenshot(region=(x, y, w, h))
            return pyautogui.screenshot()
        except Exception as e:
            print(f"screenshot error: {e}")
            return None

    def screenshot_base64(self, region=None):
        img = self.screenshot(region)
        if img is None:
            return None
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode()

    def save_screenshot(self, path=None):
        img = self.screenshot()
        if path is None:
            path = f"/tmp/hermes_screen_{int(time.time())}.png"
        img.save(path)
        return path

    def ocr(self, region=None):
        """OCR提取文字"""
        if not self._tesseract:
            return "[需要安装tesseract: brew install tesseract tesseract-lang]"
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            tmp = f.name
        try:
            img = self.screenshot(region)
            img.save(tmp)
            result = subprocess.run(
                ['tesseract', tmp, 'stdout', '-l', 'chi_sim+eng', '--psm', '6'],
                capture_output=True, text=True, timeout=15
            )
            return result.stdout.strip()
        except Exception as e:
            return f"[OCR error: {e}]"
        finally:
            try:
                os.unlink(tmp)
            except:
                pass

    def find_image(self, template_path, confidence=0.8):
        try:
            loc = pyautogui.locateOnScreen(template_path, confidence=confidence)
            if loc:
                center = pyautogui.center(loc)
                return {"found": True, "x": center.x, "y": center.y, "region": loc}
        except:
            pass
        return {"found": False}

    def get_screen_size(self):
        return pyautogui.size()

    def wait_for_image(self, template_path, timeout=10, confidence=0.8):
        start = time.time()
        while time.time() - start < timeout:
            result = self.find_image(template_path, confidence)
            if result["found"]:
                return result
            time.sleep(0.5)
        return {"found": False}


class HermesHand:
    """控制电脑"""
    def __init__(self):
        self.available = True

    def move_to(self, x, y, duration=0.3):
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, x=None, y=None, clicks=1):
        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks)
        else:
            pyautogui.click(clicks=clicks)

    def double_click(self, x=None, y=None):
        pyautogui.doubleClick(x, y)

    def right_click(self, x=None, y=None):
        pyautogui.rightClick(x, y)

    def typewrite(self, text, interval=0.05):
        pyautogui.write(text, interval=interval)

    def press(self, key):
        pyautogui.press(key)

    def hotkey(self, *keys):
        pyautogui.hotkey(*keys)

    def scroll(self, clicks, x=None, y=None):
        pyautogui.scroll(clicks, x=x, y=y)

    def drag(self, start_x, start_y, end_x, end_y, duration=0.5):
        pyautogui.moveTo(start_x, start_y)
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button='left')


class HermesReflector:
    """反思能力"""
    def __init__(self, eye):
        self.eye = eye
        self.history = []

    def record(self, action, expected):
        self.history.append({
            "action": action,
            "expected": expected,
            "time": time.time(),
            "verified": False,
            "result": None
        })

    def get_last(self):
        return self.history[-1] if self.history else None

    def verify(self, expected_phrase):
        text = self.eye.ocr()
        found = expected_phrase in text
        last = self.get_last()
        if last:
            last["verified"] = True
            last["result"] = "success" if found else "failure"
            last["actual_text"] = text[:200]
        return found

    def verify_by_screenshot(self, expected_in_image):
        path = self.eye.save_screenshot()
        last = self.get_last()
        if last:
            last["screenshot"] = path
        return path


if __name__ == "__main__":
    print("Hermes 真人化模块测试")
    mouth = HermesMouth()
    eye = HermesEye()
    hand = HermesHand()
    refl = HermesReflector(eye)

    mouth.speak("你好，我是Hermes，真人化模块测试！", emotion="happy")
    print(f"屏幕尺寸: {eye.get_screen_size()}")
    print(f"OCR可用: {eye.has_ocr}")
    refl.record("测试动作", "预期结果")
    print("✅ 全部就绪")
