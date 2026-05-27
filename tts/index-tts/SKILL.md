---
name: index-tts
description: "IndexTTS2 零样本语音合成 — 工业级可控TTS，支持情感控制、时长控制、声音克隆。触发词：indextts、IndexTTS、index-tts、哔哩哔哩TTS、情感TTS。"
permissions:
  - network
  - filesystem
required_paths:
  - /Users/aimac/index-tts
required_commands: []
required_packages:
  - uv
---

# IndexTTS2

哔哩哔哩团队开源的工业级零样本TTS，20k+ GitHub stars，支持情感解耦和时长控制。

## 核心能力

| 特性 | 说明 |
|------|------|
| 零样本声音克隆 | 从短音频(10-30秒)提取音色 |
| 情感控制 | 音色与情感解耦，可独立调节 |
| 时长控制 | 精确控制合成语音时长（对口型视频必备） |
| 多语言 | 中英文 |

## 模型下载（推荐 ModelScope，比 git lfs 快）

```python
from modelscope import snapshot_download
snapshot_download('IndexTeam/IndexTTS-2', cache_dir='~/.cache/modelscope/models')
```

## 安装（必须用 uv）

```bash
# 1. clone
git clone https://github.com/index-tts/index-tts.git
cd index-tts

# 2. git-lfs（brew install git-lfs && git lfs install）

# 3. 同步依赖
uv sync --all-extras

# 国内镜像加速
uv sync --all-extras --default-index "https://mirrors.aliyun.com/pypi/simple"
```

## 推理

```python
from indextts.infer import IndexTTS

tts = IndexTTS(
    cfg_path='checkpoints/config.yaml',
    model_dir='checkpoints',
    device='mps'  # Mac MPS / 'cuda:0' / 'cpu'
)
result = tts.infer(
    text='你好，这是测试',
    ref_audio='path/to/reference.wav',
    emotion='happy'
)
```

## Mac MPS 支持

- ✅ 代码支持 MPS（`device='mps'`）
- ⚠️ 模型太大（GPT 3.25GB），MPS 推理极慢（估计 30分钟+/句）
- **推荐工作流**：先用 HuggingFace/ModelScope **在线Demo**听效果 → 有 GPU 机器再本地部署

## 在线 Demo

- HuggingFace: https://huggingface.co/spaces/IndexTeam/IndexTTS-2-Demo
- ModelScope: https://modelscope.cn/studios/IndexTeam/IndexTTS-2-Demo

## 部署优先级建议

| 场景 | 推荐 |
|------|------|
| 快速体验 | 在线 Demo |
| 有 NVIDIA GPU (8GB+) | 本地部署，喝杯咖啡就跑完 |
| Mac 凑合跑 | 可跑，极慢，不着急可以后台跑 |
| 云 GPU | AutoDL/矩池云，1小时几块钱 |

## Pitfalls

- **必须用 uv**：`uv sync`，pip/conda 不保证依赖版本正确，且无 GPU 加速
- **git lfs 超时**：国内网络拉取大文件经常超时，用 ModelScope `snapshot_download` 更稳定
- **MPS 推理慢**：大模型在 Mac 上不适合实时使用，纯体验用途
- **权重目录**：ModelScope 下载到 `~/.cache/modelscope/models/IndexTeam/IndexTTS-2/`，需手动复制到 `checkpoints/`
