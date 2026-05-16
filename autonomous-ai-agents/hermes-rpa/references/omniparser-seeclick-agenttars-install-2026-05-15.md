# OmniParser + SeeClick + Agent TARS 安装实录（2026-05-15）

## OmniParser 安装（完整步骤）

### 1. conda 环境
```bash
conda create -n omni python=3.12 -y
conda activate omni
```

### 2. 依赖
```bash
pip install torch torchvision
pip install paddleocr==2.7.3 paddlepaddle==2.6.2
# ⚠️ paddleocr 3.x 有 show_log 参数bug，必须用 2.7.3
# ⚠️ paddlepaddle 最低 2.6.2（2.5.2 不兼容）
```

### 3. 克隆 + 权重
```bash
git clone https://github.com/hamid中人/omniparser.git ~/projects/omniparser
cd ~/projects/omniparser

# 权重下载（自动缓存到 ~/.paddleocr）
export PYTHONPATH=~/projects/omniparser
python -c "from util.omniparser import Omniparser; print('OK')"
# 首次运行会下载 OCR 模型（约14MB）
```

### 4. 启动验证
```python
PYTHONPATH=~/projects/omniparser python -c "
from util.omniparser import Omniparser
from util.utils import get_yolo_model, get_caption_model_processor
print('OmniParser ALL OK')
"
# 输出包含 paddleocr 下载进度，正常
```

### 已知坑
- `show_log=False` 参数在 paddleocr 3.x 中会 ValueError，必须降级
- 首次 import 会触发 matplotlib 字体缓存，属正常
- OCR 模型路径：`~/.paddleocr/whl/det/en/`

## SeeClick 验证

checkpoint 路径：`~/projects/SeeClick`
文件：10个 safetensors（model-00001-of-00010 ~ model-00010-of-00010）

```python
from transformers import AutoModelForCausalLM
import os
ckpt = '/Users/aimac/projects/SeeClick'
files = [f for f in os.listdir(ckpt) if f.endswith('.safetensors')]
print(f'SeeClick: {len(files)} safetensors OK')
# 输出: SeeClick: 10 safetensors OK
```

## Agent TARS CLI（UI-TARS）

### 安装
```bash
npx --yes --no-fund --no-audit @agent-tars/cli@0.3.0 --version
# 版本: 10.9.7
```

### 调用方式（npx 非全局安装）
```bash
# 每次调用
npx --yes --no-fund --no-audit @agent-tars/cli@0.3.0 <command>

# 做 shim 方便调用
mkdir -p ~/bin
cat > ~/bin/agent-tars << 'EOF'
#!/bin/bash
exec ~/.hermes/node/bin/npx --yes --no-fund --no-audit @agent-tars/cli@0.3.0 "$@"
EOF
chmod +x ~/bin/agent-tars
agent-tars --version
```

## Ollama 升级 + qwen2-vl

### 问题
- 原有 Ollama 0.23.4 太旧，不支持 qwen2-vl 系列
- `ollama pull qwen2-vl:7b` → Error: pull model manifest: file does not exist
- qwen2-vl:2b 等 tag 均不存在

### 解决
```bash
# 用官方 install.sh 升级（会自动处理）
curl -fsSL https://ollama.com/install.sh | sh
# 或手动下载：https://ollama.com/download/Ollama-darwin.zip

# 升级后版本 0.24.0

# qwen2-vl:7b 官方已下架，用 qwen2.5vl:7b（替代）
ollama pull qwen2.5vl:7b
# 大小: 6.0 GB
```

### 当前模型列表
```
qwen2.5vl:7b          6.0 GB   ← GUI VL 模型主力
ahmadwaqar/smolvlm2-agentic-gui:latest  2.0 GB
qwen3-fast:latest      5.2 GB
qwen3:8b              5.2 GB
```

## 快速启动命令汇总

```bash
# OmniParser
export PYTHONPATH=~/projects/omniparser && conda activate omni

# Agent TARS
agent-tars --version

# Ollama
ollama list | grep -E "qwen|smol"

# npx 调用 agent-tars
npx --yes --no-fund --no-audit @agent-tars/cli@0.3.0 --version
```
