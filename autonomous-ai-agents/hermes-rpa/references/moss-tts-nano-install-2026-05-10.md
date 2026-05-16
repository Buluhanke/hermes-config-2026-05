# MOSS-TTS-Nano 安装记录

**日期**: 2026-05-10
**目标**: 声音克隆 TTS，本地 CPU 运行，0.1B 参数，支持 20 种语言

## 安装状态

- **源码**: `~/MOSS-TTS-Nano/` — 已克隆
- **环境**: Python 3.12 venv at `~/MOSS-TTS-Nano/.venv312`
- **ONNX runtime**: ✅ 已安装（torch CPU / onnxruntime 已装）
- **模型文件**: ❌ Hugging Face 下载超时（代理未启动时无法访问 hf.co）

## 验证状态

```bash
cd ~/MOSS-TTS-Nano
.venv312/bin/python infer_onnx.py --help  # ✅ 帮助信息正常

# 模型下载失败（Hugging Face 访问超时）
.venv312/bin/python infer_onnx.py \
  --prompt-audio-path assets/audio/zh_1.wav \
  --text "你好，欢迎使用MOSS语音合成。" \
  --output-audio-path /tmp/moss_test.wav
# → BLOCKED (超时)
```

## 为什么值得装

| 能力 | Kokoro (已装) | MOSS-TTS-Nano |
|------|--------------|--------------|
| 声音克隆 | ❌ | ✅ 参考音频即可 |
| 本地 CPU | ✅ | ✅ 4核CPU |
| 中英日韩等 | ✅ | ✅ 20种语言 |
| ONNX 加速 | N/A | ✅ MacBook Air M4 单核实时 |

**核心差异**: Kokoro 无法做声音克隆，MOSS-TTS-Nano 可以。只要给一段参考音频（3~30秒），就能合成相似音色的语音。这是 Kokoro / Noiz 都做不到的能力。

## 下次安装步骤

```bash
# 1. 确认代理运行中（Hugging Face 必须走代理）
# 2. 激活环境
cd ~/MOSS-TTS-Nano
source .venv312/bin/activate

# 3. 推理（会自动下载模型到 ~/.cache/huggingface/ 或 ./models/）
python infer_onnx.py \
  --prompt-audio-path assets/audio/zh_1.wav \
  --text "欢迎使用MOSS语音合成" \
  --output-audio-path /tmp/moss_test.wav \
  --cpu-threads 4

# 4. Web demo
python app_onnx.py
# 打开 http://127.0.0.1:18083
```

## 集成到 Hermes 方案

未来可以通过 MCP server 包装为 `mcp_mosstts_*` 工具调用，或直接 `execute_code` 里 `subprocess.run` 调用 `infer_onnx.py`。

**当前优先级**: 低。现有 Kokoro + Noiz TTS 已够用。等真的需要声音克隆时再动。
