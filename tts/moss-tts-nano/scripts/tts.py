#!/usr/bin/env python3
"""
MOSS-TTS-Nano CLI wrapper.
Runs infer.py from MOSS-TTS-Nano dir so relative asset paths resolve correctly.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

MOSS_DIR = Path("/Users/aimac/MOSS-TTS-Nano")
MOSS_VENV_PYTHON = str(MOSS_DIR / ".venv312/bin/python")
INFER_SCRIPT = str(MOSS_DIR / "infer.py")

# Preset voices available in assets/audio/ (only existing files)
VOICE_MAP = {
    "Junhao": "assets/audio/zh_1.wav", "Xiaoyu": "assets/audio/zh_3.wav",
    "Yuewen": "assets/audio/zh_4.wav", "Lingyu": "assets/audio/zh_6.wav",
    "Minglang": "assets/audio/zh_10.wav", "Yujie": "assets/audio/zh_11.wav",
    "Ava": "assets/audio/en_2.wav", "Bella": "assets/audio/en_3.wav",
    "Adam": "assets/audio/en_4.wav", "Nathan": "assets/audio/en_6.wav",
}


def parse_args():
    parser = argparse.ArgumentParser(description="MOSS-TTS-Nano CLI")
    parser.add_argument("-t", "--text", help="Text to synthesize")
    parser.add_argument("-f", "--text-file", help="UTF-8 text file to synthesize")
    parser.add_argument("--voice-name", default="Junhao",
                        help="Preset voice name (default: Junhao)")
    parser.add_argument("--ref-audio", default=None,
                        help="Reference audio path for voice cloning")
    parser.add_argument("--prompt-text", default=None,
                        help="Transcript of reference audio")
    parser.add_argument("-o", "--output", default="/tmp/moss_tts_output.wav",
                        help="Output wav path")
    parser.add_argument("--device", default="cpu",
                        help="Device: cpu (default) / cuda / auto")
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.text and not args.text_file:
        print("Error: must provide -t TEXT or -f TEXT_FILE", file=sys.stderr)
        sys.exit(1)

    cmd = [
        MOSS_VENV_PYTHON,
        INFER_SCRIPT,
        "--device", args.device,
        "--output-audio-path", args.output,
        "--disable-wetext-processing",
        "--disable-normalize-tts-text",
    ]

    if args.text_file:
        cmd += ["--text-file", args.text_file]
    else:
        cmd += ["--text", args.text]

    if args.ref_audio:
        cmd += [
            "--mode", "voice_clone",
            "--prompt-audio-path", str(Path(args.ref_audio).resolve()),
        ]
        if args.prompt_text:
            cmd += ["--prompt-text", args.prompt_text]
    else:
        voice = args.voice_name
        if voice not in VOICE_MAP:
            available = ", ".join(VOICE_MAP.keys())
            print(f"Error: unknown voice '{voice}'. Available: {available}", file=sys.stderr)
            sys.exit(1)
        prompt_audio = VOICE_MAP[voice]  # relative, resolves from MOSS_DIR
        cmd += ["--mode", "voice_clone", "--prompt-audio-path", prompt_audio]

    result = subprocess.run(cmd, cwd=str(MOSS_DIR))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
