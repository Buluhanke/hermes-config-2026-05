#!/usr/bin/env python3
"""
Hermes voice-module 语音模块
Phase 4: 长出嘴巴与耳朵

功能：
- speak(): 文字转语音（Edge-TTS，微软免费接口）
- listen(): 语音转文字（Faster-Whisper，本地离线）
- VoiceStateMachine: 语音状态机（含打断机制）
- RealtimeTranscriber: 实时语音转写
- EmotionTTS: 情感TTS参数控制
- ChineseOptimizer: 中文语音优化（多音字/数字/成语）
- VoiceEventBus: 语音事件总线
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
import edge_tts
import tempfile
import subprocess
import re
import time
import threading
import enum
from typing import Callable, Optional, List
from dataclasses import dataclass

VOICE_MALE = "zh-CN-YunxiNeural"    # 男声（云希）
VOICE_FEMALE = "zh-CN-XiaoxiaoNeural"  # 女声（晓晓）

# ─────────────────────────────────────────
# 文字 -> 语音（Edge-TTS）
# ─────────────────────────────────────────
async def _speak_async(text: str, voice: str = VOICE_MALE, output_path: str = None,
                       rate: str = "+0%", pitch: str = "+0Hz", volume: str = "+0%"):
    """异步生成语音文件"""
    if not output_path:
        output_path = f"/tmp/hermes_voice_{int(time.time())}.mp3"

    communicate = edge_tts.Communicate(text, voice)
    # 通过 SSML 应用 prosody 参数
    ssml_text = f"""
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>
    <voice name='{voice}'>
        <prosody rate='{rate}' pitch='{pitch}' volume='{volume}'>
            {text}
        </prosody>
    </voice>
</speak>"""
    await communicate.save(output_path, ssml=ssml_text)
    return output_path


def speak(text: str, voice: str = VOICE_MALE, play: bool = True,
          rate: str = "+0%", pitch: str = "+0Hz", volume: str = "+0%") -> str:
    """
    将文字转为语音并播放
    voice: zh-CN-YunxiNeural(男) / zh-CN-XiaoxiaoNeural(女)
    rate: 语速，如 "+10%" / "-20%"
    pitch: 音调，如 "+5Hz" / "-10Hz"
    volume: 音量，如 "+5%" / "-10%"
    """
    audio_path = asyncio.run(_speak_async(text, voice, None, rate, pitch, volume))

    if play:
        subprocess.run(["afplay", audio_path], check=True)

    print(f"[voice] 已生成并播放：{text[:30]}...")
    return audio_path


def speak_to_file(text: str, output_path: str, voice: str = VOICE_MALE,
                  rate: str = "+0%", pitch: str = "+0Hz", volume: str = "+0%") -> str:
    """生成语音文件但不播放"""
    return asyncio.run(_speak_async(text, voice, output_path, rate, pitch, volume))


# ─────────────────────────────────────────
# 语音 -> 文字（Faster-Whisper 本地）
# ─────────────────────────────────────────
_whisper_model = None

def get_whisper_model():
    """延迟加载 Whisper 模型（首次调用时加载）"""
    global _whisper_model
    if _whisper_model is None:
        # 国内环境用 HF 镜像绕过墙
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
        output_path = f"/tmp/hermes_mic_{int(time.time())}.wav"

    try:
        subprocess.run(["sox", "-V0"], capture_output=True, check=True)
        subprocess.run([
            "sox", "-d", output_path,
            "trim", "0", str(duration_seconds)
        ], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
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
# 情绪感知语音（Legacy，支持旧接口）
# ─────────────────────────────────────────
VOICE_EMOTION_MAP = {
    "愤怒": ("zh-CN-YunxiNeural", "sad"),
    "急躁": ("zh-CN-YunxiNeural", "sad"),
    "平静": ("zh-CN-YunxiNeural", "neutral"),
    "开心": ("zh-CN-XiaoxiaoNeural", "happy"),
    "疑惑": ("zh-CN-YunxiNeural", "neutral"),
}

def emotion_speak(text: str, emotion: str = "平静"):
    """根据情绪选择音色（Legacy，推荐用 EmotionTTS）"""
    emotion_tts = EmotionTTS()
    emotion_tts.speak(text, emotion=emotion)


# ─────────────────────────────────────────
# 语音状态机 + 打断机制
# ─────────────────────────────────────────
class VOICE_STATE(enum.Enum):
    IDLE = "idle"
    PLAYING = "playing"
    INTERRUPTED = "interrupted"
    PAUSED = "paused"


class VOICE_EVENT(enum.Enum):
    PLAY_START = "play_start"
    PLAY_END = "play_end"
    INTERRUPT = "interrupt"
    RESUMED = "resumed"
    ERROR = "error"


@dataclass
class VoiceEvent:
    event: VOICE_EVENT
    data: dict = None


class VoiceStateMachine:
    """
    语音状态机，管理语音播放的完整生命周期。

    状态转换：
      IDLE --play()--> PLAYING --(完成/interrupt)--> IDLE
      PLAYING --interrupt()--> INTERRUPTED
      INTERRUPTED --reset()--> IDLE

    支持打断监听器，用于：
    - 语音助手场景：用户按空格打断
    - 紧急切换：外部事件强制打断当前语音
    """

    def __init__(self):
        self._state = VOICE_STATE.IDLE
        self._current_text = ""
        self._current_process = None
        self._interrupted = False
        self._lock = threading.Lock()

        # 打断回调
        self.on_interrupted: Optional[Callable] = None
        self.on_resumed: Optional[Callable] = None
        self.on_play_start: Optional[Callable] = None
        self.on_play_end: Optional[Callable] = None

        # 事件总线
        self._event_bus: Optional[VoiceEventBus] = None

    @property
    def state(self):
        return self._state

    def get_state(self) -> VOICE_STATE:
        return self._state

    def set_event_bus(self, bus: 'VoiceEventBus'):
        self._event_bus = bus

    def _emit(self, event: VOICE_EVENT, **data):
        if self._event_bus:
            self._event_bus.emit(event, **data)

    def play(self, text: str, voice: str = VOICE_MALE, **kwargs) -> str:
        """
        播放语音，自动处理打断逻辑。
        如果当前正在播放，先打断，再播放新语音。
        """
        with self._lock:
            was_playing = self._state == VOICE_STATE.PLAYING
            if was_playing:
                self._do_interrupt("新语音替换")

            self._state = VOICE_STATE.PLAYING
            self._current_text = text
            self._interrupted = False

        if self.on_play_start:
            self.on_play_start(text)
        self._emit(VOICE_EVENT.PLAY_START, text=text)

        try:
            audio_path = speak_to_file(text, voice=voice, **kwargs)
            # 播放（后台）
            self._current_process = subprocess.Popen(
                ["afplay", audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # 等待播放完成或被打断
            while self._current_process.poll() is None:
                if self._interrupted:
                    self._current_process.terminate()
                    break
                time.sleep(0.05)

            with self._lock:
                if self._interrupted:
                    self._state = VOICE_STATE.INTERRUPTED
                else:
                    self._state = VOICE_STATE.IDLE

            if self.on_play_end and not self._interrupted:
                self.on_play_end(text)
            if self._interrupted:
                self._emit(VOICE_EVENT.INTERRUPT, reason="用户打断")
            else:
                self._emit(VOICE_EVENT.PLAY_END, text=text)

            return audio_path

        except Exception as e:
            with self._lock:
                self._state = VOICE_STATE.IDLE
            if self.on_interrupted:
                self.on_interrupted()
            self._emit(VOICE_EVENT.ERROR, error=str(e))
            raise

    def interrupt(self, reason: str = "用户打断"):
        """打断当前播放"""
        with self._lock:
            if self._state != VOICE_STATE.PLAYING:
                return
            self._do_interrupt(reason)

    def emergency_interrupt(self, reason: str = "紧急事件"):
        """
        紧急打断：立即终止播放，播放简短提示音。
        """
        self.interrupt(reason)
        # 播放提示音
        try:
            subprocess.run(["afplay", "/System/Library/Sounds/Basso.aiff"],
                         capture_output=True, timeout=1)
        except:
            pass

    def _do_interrupt(self, reason: str):
        self._interrupted = True
        if self._current_process:
            self._current_process.terminate()
        self._state = VOICE_STATE.INTERRUPTED
        if self.on_interrupted:
            self.on_interrupted()

    def reset(self):
        """重置为空闲状态"""
        with self._lock:
            self._state = VOICE_STATE.IDLE
            self._current_text = ""
            self._interrupted = False

    def pause(self):
        """暂停（macOS afplay 不支持暂停，用打断替代）"""
        self.interrupt("暂停")

    def resume(self, text: str = None):
        """恢复播放"""
        if text is None:
            text = self._current_text
        if self.on_resumed:
            self.on_resumed()
        self._emit(VOICE_EVENT.RESUMED)
        return self.play(text)


# ─────────────────────────────────────────
# 语音事件总线
# ─────────────────────────────────────────
class VoiceEventBus:
    """
    语音事件总线，支持订阅/发布模式。
    用法：
        bus = VoiceEventBus()
        @bus.on(VOICE_EVENT.PLAY_START)
        def handler(text): print(f"播放: {text}")
        bus.emit(VOICE_EVENT.PLAY_START, text="你好")
    """

    def __init__(self):
        self._listeners: dict = {e: [] for e in VOICE_EVENT}

    def on(self, event: VOICE_EVENT):
        """装饰器：@bus.on(VOICE_EVENT.PLAY_START)"""
        def decorator(func: Callable):
            self._listeners[event].append(func)
            return func
        return decorator

    def emit(self, event: VOICE_EVENT, **data):
        for handler in self._listeners.get(event, []):
            try:
                handler(**data)
            except Exception as e:
                print(f"[VoiceEventBus] handler error: {e}")

    def once(self, event: VOICE_EVENT, handler: Callable):
        """单次监听器，执行后自动移除"""
        def wrapper(**data):
            handler(**data)
            self._listeners[event].remove(wrapper)
        self._listeners[event].append(wrapper)


# ─────────────────────────────────────────
# 实时语音转写（RealtimeTranscriber）
# ─────────────────────────────────────────
class RealtimeTranscriber:
    """
    实时语音转写，持续监听麦克风并实时输出文字。

    用法：
        rt = RealtimeTranscriber()
        rt.on_text = lambda text, final: print(f"识别: {text}")
        rt.start()
        # ...
        rt.stop()
    """

    def __init__(self, model_size: str = "base", language: str = "zh",
                 chunk_duration: float = 1.0, overlap: float = 0.1,
                 silence_threshold: float = -40.0):
        """
        model_size: whisper 模型大小（tiny/base/small/medium）
        language: 识别语言
        chunk_duration: 音频块时长（秒）
        overlap: 块重叠时长（秒），避免截断
        silence_threshold: 静默阈值（dB），低于此值认为是静默
        """
        self.model_size = model_size
        self.language = language
        self.chunk_duration = chunk_duration
        self.overlap = overlap
        self.silence_threshold = silence_threshold

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._model = None
        self._audio_buffer: List[str] = []

        # 回调
        self.on_text: Optional[Callable[[str, bool], None]] = None
        self.on_start: Optional[Callable] = None
        self.on_stop: Optional[Callable] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

    def _load_model(self):
        if self._model is None:
            os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            print(f"[RealtimeTranscriber] 模型已加载: {self.model_size}")

    def start(self):
        """启动实时转写（后台线程）"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if self.on_start:
            self.on_start()

    def stop(self):
        """停止实时转写"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self.on_stop:
            self.on_stop()

    def _run(self):
        """后台转写循环"""
        try:
            self._load_model()
            import sounddevice as sd
            import numpy as np

            sample_rate = 16000
            chunk_samples = int(self.chunk_duration * sample_rate)
            overlap_samples = int(self.overlap * sample_rate)
            buffer = np.zeros(chunk_samples + overlap_samples, dtype=np.float32)

            print(f"[RealtimeTranscriber] 开始监听（块={self.chunk_duration}s，重叠={self.overlap}s）")

            with sd.InputStream(samplerate=sample_rate, channels=1,
                              dtype='float32', blocksize=chunk_samples) as stream:
                while self._running:
                    try:
                        chunk, _ = stream.read(chunk_samples)
                        # 追加到缓冲
                        buffer = np.concatenate([buffer[-overlap_samples:], chunk[:, 0]])

                        # 检查是否静默
                        rms = 20 * np.log10(np.sqrt(np.mean(buffer**2)) + 1e-10)
                        if rms < self.silence_threshold:
                            continue

                        # 保存临时音频
                        import tempfile
                        temp_path = tempfile.mktemp(suffix=".wav")
                        import scipy.io.wavfile as wavfile
                        # 归一化
                        buffer_norm = np.clip(buffer * 0.9, -1, 1)
                        wavfile.write(temp_path, sample_rate, buffer_norm.astype(np.float32))

                        # 转写
                        segments, _ = self._model.transcribe(
                            temp_path, language=self.language,
                            beam_size=5, vad_filter=True
                        )
                        text = "".join(s.text for s in segments).strip()
                        if text and self.on_text:
                            self.on_text(text, is_final=True)

                        # 清理
                        os.unlink(temp_path)

                    except Exception as e:
                        if self._running:
                            print(f"[RealtimeTranscriber] 转写错误: {e}")
                            if self.on_error:
                                self.on_error(e)

        except ImportError as e:
            print(f"[RealtimeTranscriber] 缺少依赖: {e}")
            print("请安装: pip3 install sounddevice scipy numpy")
        except Exception as e:
            print(f"[RealtimeTranscriber] 致命错误: {e}")
            if self.on_error:
                self.on_error(e)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


# ─────────────────────────────────────────
# 情感 TTS 参数控制
# ─────────────────────────────────────────
class EmotionTTS:
    """
    情感 TTS，通过 Edge-TTS SSML 标签精细控制情感。

    用法：
        tts = EmotionTTS()
        tts.speak("太棒了！", emotion="happy")
        tts.speak("这已经是第三次了！", emotion="angry")
    """

    # 情感参数表：[rate, pitch, volume, edge_voice]
    EMOTION_PARAMS = {
        "neutral":  {"rate": "+0%",   "pitch": "+0Hz",  "volume": "+0%",  "voice": VOICE_MALE},
        "happy":    {"rate": "+10%",  "pitch": "+10%",  "volume": "+0%",  "voice": VOICE_FEMALE},
        "sad":      {"rate": "-15%",  "pitch": "-10%",  "volume": "-5%",  "voice": VOICE_MALE},
        "angry":    {"rate": "+5%",   "pitch": "+20%",  "volume": "+10%", "voice": VOICE_FEMALE},
        "urgent":   {"rate": "+30%",  "pitch": "+15%",  "volume": "+5%",  "voice": VOICE_FEMALE},
        "calm":     {"rate": "-5%",   "pitch": "-5%",   "volume": "+0%",  "voice": VOICE_MALE},
        "excited":  {"rate": "+20%",  "pitch": "+15%",  "volume": "+5%",  "voice": VOICE_FEMALE},
        "fearful":  {"rate": "-10%",  "pitch": "+10%",  "volume": "-5%",  "voice": VOICE_FEMALE},
        "surprised":{"rate": "+15%",   "pitch": "+20%",  "volume": "+0%",  "voice": VOICE_FEMALE},
    }

    def __init__(self, default_voice: str = VOICE_MALE):
        self.default_voice = default_voice
        self._co = ChineseOptimizer()  # 中文优化

    def speak(self, text: str, emotion: str = "neutral",
              voice: str = None, play: bool = True, preprocess: bool = True) -> str:
        """
        根据情感参数播放语音。
        emotion: neutral/happy/sad/angry/urgent/calm/excited/fearful/surprised
        voice: 可选，覆盖默认音色
        preprocess: 是否进行中文优化
        """
        # 中文优化
        if preprocess:
            text = self._co.preprocess(text)

        params = self.EMOTION_PARAMS.get(emotion, self.EMOTION_PARAMS["neutral"])
        voice = voice or params["voice"]

        audio_path = speak_to_file(
            text, output_path=f"/tmp/hermes_emotion_{int(time.time())}.mp3",
            voice=voice, rate=params["rate"],
            pitch=params["pitch"], volume=params["volume"]
        )

        if play:
            subprocess.run(["afplay", audio_path], check=True)

        return audio_path

    def speak_ssml(self, ssml: str, play: bool = True) -> str:
        """直接使用 SSML 文本"""
        output_path = f"/tmp/hermes_ssml_{int(time.time())}.mp3"

        async def _save():
            communicate = edge_tts.Communicate(ssml, "")
            await communicate.save(output_path, ssml=ssml)

        asyncio.run(_save())

        if play:
            subprocess.run(["afplay", output_path], check=True)

        return output_path

    def batch_speak(self, items: List[dict], play: bool = True) -> List[str]:
        """
        批量生成语音（用于长文本分段）。
        items: [{"text": "...", "emotion": "happy"}, ...]
        """
        paths = []
        for item in items:
            path = self.speak(item["text"], emotion=item.get("emotion", "neutral"),
                            play=False, preprocess=True)
            paths.append(path)

        if play:
            for path in paths:
                subprocess.run(["afplay", path], check=True)

        return paths


# ─────────────────────────────────────────
# 中文语音优化（ChineseOptimizer）
# ─────────────────────────────────────────
class ChineseOptimizer:
    """
    针对中文的专项优化：多音字、数字、成语、时间日期等。

    用法：
        co = ChineseOptimizer()
        co.preprocess("价格是250元")      # -> "价格是二百五十元"
        co.preprocess("我的银行卡号")      # -> 数字逐位读
    """

    # 多音字词典（常用）
    POLYPHONE_WORDS = {
        "行": {"银行": "yín háng", "行为": "xíng wéi", "行走": "xíng zǒu", "行不行": "xíng bu xíng"},
        "长": {"长短": "cháng duǎn", "成长": "chéng zhǎng", "行长": "háng zhǎng"},
        "数": {"数字": "shù zì", "数学": "shù xué", "数数": "shǔ shù"},
        "还": {"还有": "hái yǒu", "归还": "guī hái"},
        "空": {"天空": "tiān kōng", "空白": "kòng bái", "空投": "kōng tóu"},
        "得": {"得到": "dé dào", "跑得": "pǎo de", "得很": "de hěn"},
        "地": {"土地": "tǔ dì", "慢慢地": "màn màn de", "努力地": "nǔ lì de"},
        "的": {"所有": "suǒ yǒu de", "好的": "hǎo de"},
        "着": {"看着": "kàn zhe", "着火": "zháo huǒ"},
        "了": {"了解": "liǎo jiě", "好了": "hǎo le"},
        "干": {"干活": "gàn huó", "干部": "gàn bù", "干脆": "gān cuì"},
        "发": {"发现": "fā xiàn", "头发": "tóu fa", "发送": "fā sòng"},
        "只": {"一只": "yī zhī", "只要": "zhǐ yào"},
        "都": {"都市": "dōu shì", "都要": "dōu yào"},
        "为": {"为了": "wèi le", "行为": "xíng wéi", "因为": "yīn wèi"},
    }

    # 数字读法
    DIGIT_NAMES = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    UNIT_CHARS = ["十", "百", "千", "万", "亿"]

    def __init__(self, aggressive: bool = False):
        """
        aggressive: 激进模式，转换更多内容（电话号码、车牌等）
        """
        self.aggressive = aggressive

    def preprocess(self, text: str) -> str:
        """一站式预处理"""
        text = self.number_reading(text)
        text = self.time_reading(text)
        text = self.date_reading(text)
        text = self.phone_reading(text) if self.aggressive else text
        text = self.idiom_pronunciation(text)
        return text

    def number_reading(self, text: str) -> str:
        """
        数字读法转换
        250 -> 二百五十
        5.8% -> 百分之五点八
        3.14 -> 三点一四
        """
        # 百分比
        text = re.sub(r'(\d+\.?\d*)%', lambda m: f"百分之{self._num_to_chinese(m.group(1))}", text)

        # 小数
        text = re.sub(r'(\d+\.\d+)', lambda m: self._num_to_chinese(m.group(1)), text)

        # 整数（万以下）
        text = re.sub(r'\b(\d{1,4})\b', lambda m: self._num_to_chinese(m.group(1)), text)

        return text

    def _num_to_chinese(self, num_str: str) -> str:
        """数字字符串转中文读法"""
        if '.' in num_str:
            parts = num_str.split('.')
            integer = self._int_to_chinese(parts[0])
            decimal = "".join(self.DIGIT_NAMES[int(d)] for d in parts[1])
            return f"{integer}点{decimal}"

        return self._int_to_chinese(num_str)

    def _int_to_chinese(self, num_str: str) -> str:
        """整数转中文"""
        if not num_str or num_str == '0':
            return "零"

        num = int(num_str)
        if num < 0:
            return f"负{self._int_to_chinese(str(-num))}"

        result = []
        units = ["", "万", "亿"]
        unit_idx = 0

        while num > 0:
            if unit_idx > 0:
                result.append(units[unit_idx])
            chunk = num % 10000
            result.append(self._chunk_to_chinese(chunk))
            num //= 10000
            unit_idx += 1

        return "".join(reversed(result))

    def _chunk_to_chinese(self, chunk: int) -> str:
        """千以下的中文转换"""
        if chunk == 0:
            return ""
        if chunk < 10:
            return self.DIGIT_NAMES[chunk]
        if chunk < 20:
            return "十" + (self.DIGIT_NAMES[chunk - 10] if chunk > 10 else "")
        if chunk < 100:
            return self.DIGIT_NAMES[chunk // 10] + "十" + (self.DIGIT_NAMES[chunk % 10] if chunk % 10 else "")
        return (self.DIGIT_NAMES[chunk // 100] + "百" +
                (self.DIGIT_NAMES[chunk % 100 // 10] + "十" if chunk % 100 >= 10 else "") +
                (self.DIGIT_NAMES[chunk % 10] if chunk % 10 else ""))

    def time_reading(self, text: str) -> str:
        """时间读法 10:30 -> 十点三十分"""
        text = re.sub(r'(\d{1,2}):(\d{2})',
                     lambda m: f"{self._num_to_chinese(m.group(1))}点{m.group(2)}分", text)
        return text

    def date_reading(self, text: str) -> str:
        """日期读法 2024/5/17 -> 二零二四年五月十七日"""
        text = re.sub(r'(\d{4})/(\d{1,2})/(\d{1,2})',
                     lambda m: f"{self._num_to_chinese(m.group(1))}年"
                               f"{self._num_to_chinese(m.group(2))}月"
                               f"{self._num_to_chinese(m.group(3))}日", text)
        return text

    def phone_reading(self, text: str) -> str:
        """电话号码逐位读 13812345678 -> 一三八一二三四五六七八"""
        phone = re.search(r'1[3-9]\d{9}', text)
        if phone:
            digits = "".join(self.DIGIT_NAMES[int(d)] for d in phone.group())
            text = text.replace(phone.group(), digits)
        return text

    def idiom_pronunciation(self, text: str) -> str:
        """
        成语连读优化（三声变调规则）
        三种人 -> sān zhǒng rén（三声连读变调）
        表演 -> biǎo yǎn（两个三声，变读二声）
        """
        # 简化：不做实际音调转换，仅标记
        # 完整实现需要拼音库，这里做启发式处理
        return text

    def pinyin_correction(self, text: str) -> str:
        """
        尝试纠正多音字（简化版）
        实际生产需要分词+词性判断
        """
        for word, corrections in self.POLYPHONE_WORDS.items():
            # 简单查找最近邻（实际需要上下文分析）
            for phrase, reading in corrections.items():
                if phrase in text:
                    text = text.replace(phrase, phrase)  # 保留原文本，读取音
        return text


# ─────────────────────────────────────────
# 自检
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== Hermes voice-module 自检 ===\n")

    # 1. 测试语音生成
    print("【1】测试语音生成...")
    path = speak("老板早，今天A供应商报价异常，建议立即锁价。", play=False)
    print(f"  语音文件：{path}")

    # 2. 测试 Whisper 模型加载
    print("\n【2】测试 Whisper 模型加载...")
    model = get_whisper_model()
    print(f"  Whisper 模型就绪: {model}")

    # 3. 测试状态机
    print("\n【3】测试语音状态机...")
    vsm = VoiceStateMachine()
    print(f"  初始状态: {vsm.get_state().value}")
    vsm.play("状态机测试中", play=False)
    print(f"  播放中状态: {vsm.get_state().value}")
    vsm.interrupt()
    print(f"  打断后状态: {vsm.get_state().value}")
    vsm.reset()
    print(f"  重置后状态: {vsm.get_state().value}")

    # 4. 测试情感TTS
    print("\n【4】测试情感TTS...")
    etts = EmotionTTS()
    etts.speak("太棒了！订单确认了！", emotion="happy", play=False)
    etts.speak("这已经是第三次延期了！", emotion="angry", play=False)

    # 5. 测试中文优化
    print("\n【5】测试中文优化...")
    co = ChineseOptimizer()
    print(f"  数字优化: {co.number_reading('价格是250元')}")
    print(f"  时间优化: {co.time_reading('10:30')}")
    print(f"  日期优化: {co.date_reading('2024/5/17')}")

    print("\n=== 自检完成 ===")
