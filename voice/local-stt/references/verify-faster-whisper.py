#!/usr/bin/env python3
"""faster-whisper 快速验证脚本"""
import sys
import os

def main():
    os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS', '1')

    # 1. 导入验证
    try:
        from faster_whisper import WhisperModel
        print(f'✓ faster-whisper 导入成功')
    except ImportError as e:
        print(f'✗ 导入失败: {e}')
        print('  修复: pip3 install faster-whisper')
        sys.exit(1)

    # 2. 模型加载（CPU int8）
    try:
        model = WhisperModel('small', device='cpu', compute_type='int8')
        print(f'✓ 模型加载成功 (device=cpu, compute_type=int8)')
    except Exception as e:
        print(f'✗ 模型加载失败: {e}')
        sys.exit(1)

    # 3. 生成测试音调
    try:
        import struct, wave, math
        sample_rate, duration = 16000, 3
        with wave.open('/tmp/fw_test.wav', 'w') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(sample_rate)
            for i in range(sample_rate * duration):
                val = int(8000 * math.sin(2 * math.pi * 440 * i / sample_rate))
                f.writeframes(struct.pack('<h', val))
        print(f'✓ 测试音频生成完成')
    except Exception as e:
        print(f'✗ 音频生成失败: {e}')
        sys.exit(1)

    # 4. 转写验证
    try:
        segments, info = model.transcribe('/tmp/fw_test.wav', language='zh', beam_size=1)
        info = info  # consume iterator
        print(f'✓ 转写成功 (语言={info.language}, 置信度={info.language_probability:.2f})')
    except Exception as e:
        print(f'✗ 转写失败: {e}')
        sys.exit(1)

    print('\n=== all checks passed ===')

if __name__ == '__main__':
    main()
