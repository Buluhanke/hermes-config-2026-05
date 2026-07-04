---
name: voice-agent-setup
description: Set up a real-time, interruptible voice conversation agent on Hermes (macOS) using open-source components (Pipecat, Silero VAD, faster-whisper, edge-tts) to achieve FlowyAIPC-style natural dialogue with barge-in.
version: 1.0.0
created: 2026-06-30
updated: 2026-06-30
type: setup
category: meta
umbrella_of: proactive-execution
---

# Hermes Voice Agent Setup Skill

**Purpose**: Set up a real-time, interruptible voice conversation agent on Hermes (macOS) by building upon existing TTS capabilities and adding missing STT/VAD components for FlowyAIPC-style natural dialogue.

## 🔍 First: Check Existing Capabilities

Before installing new components, verify what's already available:

1. **TTS is already present**:
   - `edge-tts` tool and package are installed (Microsoft Edge TTS, free, no API key)
   - `text_to_speech` tool is available in Hermes
   - Confirm: `ls ~/.hermes/hermes-agent/venv/bin/ | grep edge`

2. **What's missing for full duplex voice**:
   - Speech-to-Text (STT) capability
   - Voice Activity Detection (VAD) for barge-in
   - Real-time orchestration layer

## 🎯 When to Use
- User wants Hermes to "speak" and listen continuously with interruptions.
- User references "FlowyAIPC", "real-time voice agent", "barge-in".
- Existing TTS is present but interactive voice dialogue is missing.

## 🛠️ Setup Steps

1. **Install Python dependencies** (in Hermes venv):
   ```bash
   source ~/.hermes/hermes-agent/venv/bin/activate
   pip install --quiet 'faster-whisper' 'silero-vad' 'pipecat-ai[whisper,silero]' aiohttp torch sounddevice
   ```

2. **Verify installed packages**:
   ```bash
   python3 -c "import faster_whisper, silero_vad; from pipecat.audio.vad.silero import SileroVADAnalyzer; print('OK')"
   ```

3. **Deploy the voice bridge script** (placed at `~/.hermes/scripts/hermes_voice_bridge.py`):
   - The script implements:
     - Silero VAD for voice activity detection.
     - Faster-Whisper (small model) for streaming STT.
     - Hermes CLI (`hermes -z "<prompt>" chat --yolo -Q`) for LLM inference (reuses existing auth/model routing).
     - Edge-TTS for TTS output, writing to a temporary MP3 and playing via `afplay` (barge-in supported via VAD-triggered termination).
   - Ensure the script is executable: `chmod +x ~/.hermes/scripts/hermes_voice_bridge.py`.

4. **Test the pipeline** (text-triggered to skip mic):
   ```bash
   cd ~/.hermes/hermes-agent && source venv/bin/activate && \
   python3 ~/.hermes/scripts/hermes_voice_bridge.py --text "用一句话介绍自己" --no-tts
   ```
   Expect Whisper load, then Hermes response.

5. **Enable microphone loop** (optional, for full duplex):
   - Edit `hermes_voice_bridge.py` and set `--no-mic` to `False` (or remove flag).
   - Ensure microphone access granted in System Settings → Privacy & Security → Microphone.
   - Run the script without `--no-tts` to hear spoken replies.

6. **Integrate with Hermes** (optional):
   - Create a skill wrapper or alias: `hermes voice-chat` could invoke the script.
   - For persistent use, consider adding a cron job or launching as a background service via `hermes computer-use` session.

## ⚠️ Pitfalls & Troubleshooting
- **Whisper model first-load delay**: The small model (~500 MB) may take 20-30s on first run; subsequent starts are <2s.
- **Microphone permissions**: If no audio input, check macOS mic grant for the terminal/Python process.
- **TTS broken pipe**: The script writes to a temp file before `afplay` to avoid stdin pipe issues with `edge-tts`.
- **Barge-in latency**: VAD triggers immediately on speech; ensure `silero_vad` sensitivity is appropriate (default works).
- **Hermes gateway availability**: The script relies on `hermes` CLI; ensure `hermes` is in PATH and you are logged in (API keys set via `.env`).

## 📚 References
- Pipecat documentation: https://pipecat.ai/
- Silero VAD: https://github.com/snakers4/silero-vad
- Faster-Whisper: https://github.com/SYSTRAN/faster-whisper
- Edge-TTS: https://github.com/rany2/edge-tts
- Hermes CLI: built-in

## ✅ Success Criteria
- User speaks into mic → system detects speech → transcribes → queries Hermes via CLI → receives text response → speaks back via speaker with <1s end-to-end latency (excluding Whisper first-load).
- User can interrupt TTS by speaking again (barge-in works).
- No external API keys required beyond those already configured for Hermes (uses existing LLM routing).

## 🔄 Maintenance
- Update Whisper model to `medium` or `large` if higher accuracy needed (trade-off latency).
- Switch to `Parakeet` MLX STT for Apple Silicon native acceleration when available.
- Replace edge-tts with local TTS (e.g., Coqui/TTS) for offline-only setups.

---