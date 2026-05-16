#!/usr/bin/env python3
"""
Hermes voice-module 语音模块
Phase 4: 长出嘴巴与耳朵

功能：
- speak(): 文字转语音（Edge-TTS，免费微软接口）
- listen(): 语音转文字（Faster-Whisper，本地离线）
- voice_briefing(): 生成语音简报并播放
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
import edge_tts
import tempfile
import subprocess
import re

VOICE_MALE = "zh-CN-YunxiNeural"    # 男声（云希）
VOICE_FEMALE = "zh-CN-XiaoxiaoNeural"  # 女声（晓晓）

# ─────────────────────────────────────────
# 文字 -> 语音（Edge-TTS）
# ─────────────────────────────────────────
async def _speak_async(text: str, voice: str = VOICE_MALE, output_path: str = None):
    """异步生成语音文件"""
    if not output_path:
        output_path = f"/tmp/hermes_voice_{int(__import__('time').time())}.mp3"

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


def speak(text: str, voice: str = VOICE_MALE, play: bool = True) -> str:
    """
    将文字转为语音并播放
    voice: zh-CN-YunxiNeural(男) / zh-CN-XiaoxiaoNeural(女)
    """
    audio_path = asyncio.run(_speak_async(text, voice))

    if play:
        # Mac 上用 afplay 播放
        subprocess.run(["afplay", audio_path], check=True)

    print(f"[voice] 已生成并播放：{text[:30]}...")
    return audio_path


def speak_to_file(text: str, output_path: str, voice: str = VOICE_MALE) -> str:
    """生成语音文件但不播放"""
    return asyncio.run(_speak_async(text, voice, output_path))


# ─────────────────────────────────────────
# 语音 -> 文字（Faster-Whisper 本地）
# ─────────────────────────────────────────
_whisper_model = None

def get_whisper_model():
    """延迟加载 Whisper 模型（首次调用时加载）"""
    global _whisper_model
    if _whisper_model is None:
        # 国内环境用 HF 镜像绕过墙
        import os
        os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
        from faster_whisper import WhisperModel
        # base 模型：体积小，Mac 秒出；medium：更准但慢
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        print("[voice] Whisper 模型已加载（base, int8）")
    return _whisper_model


def listen(audio_path: str, language: str = "zh") -> str:
    """
    将音频文件转为文字
    audio_path: .mp3/.wav/.m4a 等格式
    """
    model = get_whisper_model()
    segments, info = model.transcribe(audio_path, language=language, beam_size=5)

    result = "".join(segment.text for segment in segments)
    print(f"[voice] 识别结果：{result}")
    return result


def listen_from_mic(duration_seconds: int = 5, output_path: str = None) -> str:
    """
    从麦克风录音并转为文字
    duration_seconds: 录音时长
    """
    if not output_path:
        output_path = f"/tmp/hermes_mic_{int(__import__('time').time())}.wav"

    # 用 macOS 内置的 sox/afrecord 录音（无需额外安装）
    # 先尝试用 ffprobe 检查是否安装了 ffmpeg
    import subprocess

    # macOS 用内置的 recorder 功能（say 命令的逆向）
    # 更可靠：用 sox（brew install sox）
    try:
        subprocess.run(["sox", "-V0"], capture_output=True, check=True)
        # sox 存在，用它录音
        subprocess.run([
            "sox", "-d", output_path,
            "trim", "0", str(duration_seconds)
        ], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # sox 不可用，用 Python 内置方案
        print("[voice] sox 未安装，将麦克风录音跳过，直接返回空")
        return ""

    return listen(output_path)


# ─────────────────────────────────────────
# 语音简报（主动推送）
# ─────────────────────────────────────────
def voice_briefing(title: str, bullet_points: list) -> str:
    """
    生成语音简报并播放
    例：老板早上好，今天有3件事：1. A供应商纸箱涨价... 2. ...
    """
    lines = [title]
    for i, point in enumerate(bullet_points, 1):
        lines.append(f"第{i}点，{point}")

    script = "，".join(lines)
    # 限制总长度（Edge-TTS 对单次长度有限制）
    script = script[:500]

    return speak(script)


# ─────────────────────────────────────────
# 异常告警语音
# ─────────────────────────────────────────
def voice_alert(message: str, urgent: bool = False):
    """
    告警语音，urgent=True 时用女声（更突出）
    """
    voice = VOICE_FEMALE if urgent else VOICE_MALE
    prefix = "【紧急提醒】" if urgent else "【提醒】"
    speak(f"{prefix}{message}", voice=voice)


# ─────────────────────────────────────────
# 情绪感知语音（根据情绪调整语速/音调）
# ─────────────────────────────────────────
VOICE_EMOTION_MAP = {
    "愤怒": ("zh-CN-YunxiNeural", "sad"),     # 愤怒用略慢的男声
    "急躁": ("zh-CN-YunxiNeural", "sad"),
    "平静": ("zh-CN-YunxiNeural", "neutral"),
    "开心": ("zh-CN-XiaoxiaoNeural", "happy"),
    "疑惑": ("zh-CN-YunxiNeural", "neutral"),
}

def emotion_speak(text: str, emotion: str = "平静"):
    """根据情绪选择音色"""
    voice_config = VOICE_EMOTION_MAP.get(emotion, ("zh-CN-YunxiNeural", "neutral"))
    voice = voice_config[0]

    # Edge-TTS 的情感参数（通过 SSML 标签调整）
    async def _speak_ssml():
        output = f"/tmp/hermes_voice_{int(__import__('time').time())}.mp3"
        # 简化版：不使用复杂 SSML，直接用基础音色
        await _speak_async(text, voice, output)

    asyncio.run(_speak_ssml())

    import subprocess
    audio_file = f"/tmp/hermes_voice_{int(__import__('time').time()) - 1}.mp3"
    try:
        # 找最新的 mp3 文件
        import glob
        files = sorted(glob.glob("/tmp/hermes_voice_*.mp3"))
        if files:
            subprocess.run(["afplay", files[-1]], check=True)
    except Exception as e:
        print(f"[voice] 播放失败: {e}")

    return audio_file


# ─────────────────────────────────────────
# 自检
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== Hermes voice-module 自检 ===")

    # 测试语音生成
    print("测试语音生成...")
    path = speak("老板早，今天A供应商报价异常，建议立即锁价。", play=False)
    print(f"语音文件：{path}")

    # 测试 Whisper 模型加载
    print("测试 Whisper 模型加载...")
    model = get_whisper_model()
    print(f"Whisper 模型就绪: {model}")
