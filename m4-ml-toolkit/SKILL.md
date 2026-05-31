---
name: m4-ml-toolkit
description: M4 Mac (Apple Silicon) 本地ML工具箱 — PyTorch + MPS加速、YOLOv8、rembg去背景、OCR、模型管理、内存优化
triggers:
  - M4 Mac ML
  - Apple Silicon 深度学习
  - PyTorch MPS
  - 本地模型
  - ML环境配置
  - 模型内存优化
  - Apple Metal
---

# M4 Mac ML Toolkit

M4 Mac (24GB RAM) 的本地深度学习工具箱。所有推理跑在 Apple Silicon 的 MPS 上，无需 GPU 云。

## 环境概览

```
系统 Python:  /usr/local/bin/python3 (3.14.4)
ML 运行环境:  ~/.hermes/hermes-agent/venv (Python 3.11)
GPU 加速:     MPS (Metal Performance Shaders) ✅
```

激活命令: `source ~/.hermes/hermes-agent/venv/bin/activate`

## 已安装的工具链

| 工具 | 安装命令 | 模型缓存位置 | 状态 |
|------|---------|-------------|------|
| **PyTorch 2.12** | venv 自帶 | — | ✅ MPS |
| **torchvision 0.27** | `uv pip install torchvision` | — | ✅ |
| **transformers 5.9** | `uv pip install transformers` | ~/.cache/huggingface/ | ✅ |
| **Ultralytics YOLOv8** | `uv pip install ultralytics` | 当前目录 | ✅ 170ms |
| **rembg 2.0** | `uv pip install rembg` | ~/.u2net/ (176MB) | ✅ 2.2s |
| **PaddleOCR** | hermes-agent 已有 | ~/.paddleocr/ | ✅ |
| **scikit-image** | `uv pip install scikit-image` | — | ✅ |

## 已知问题

### 🔥 qwen3-vl:2b Ollama 模型 占用 16.7GB 内存

**症状**: Ollama 进程 RSS 达 16.5GB，系统只剩 20% 空闲内存，开始使用 swap。

**根因**: qwen3-vl:2b 在 Ollama 中加载后占用 size_vram=16.7GB（实测 RSS 16.5GB）。

**解法**: 不需要时卸载：
```bash
ollama rm qwen3-vl:2b          # 彻底删除
# 或
curl -X POST http://localhost:11434/api/generate -d '{"model":"qwen3-vl:2b","keep_alive":0}'   # 仅卸载
```

**替代方案**: YOLOv8 (170ms) + rembg (2.2s) + PaddleOCR 组合已覆盖 VLM 的大部分功能，且总占用不到 500MB。

### Nous Portal deepseek-v4-flash 模型状态变化

**背景**: 2026-05-21~22 期间，Nous Portal 的 `deepseek/deepseek-v4-flash` 免费可用（272 次会话记录，billing_provider=nous）。
但到 2026-05-31 测试时，该模型返回 404 "requires available credits"。

**教训**: 模型定价会变化。测试前不要假设收费策略与历史配置一致。

**验证方法**: 
```python
# 用 OAuth token 直接测试
auth = json.load(open("~/.hermes/shared/nous_auth.json"))
resp = urllib.request.urlopen(
    urllib.request.Request("https://inference-api.nousresearch.com/v1/chat/completions",
        data=json.dumps({"model":"deepseek/deepseek-v4-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":5}).encode(),
        headers={"Authorization":f"Bearer {auth['access_token']}","Content-Type":"application/json"},
        method="POST"))
# 200=免费可用, 404=需付费, 401=认证过期
```

### 包安装到不同 Python 环境

`uv pip install` 默认装到 venv (Python 3.11)，而系统 `python3` 是 3.14。
```bash
source ~/.hermes/hermes-agent/venv/bin/activate   # 先激活再装
```

## 内存管理清单

M4 Mac 24GB 内存分配建议：

| 进程 | 建议状态 | 说明 |
|------|---------|------|
| Ollama 服务 | 保留 (~75MB) | 常驻，但不要加载大模型 |
| qwen3-vl:2b | **卸载** ⚠️ | 占用 16.7GB，用 YOLO/rembg 替代 |
| qwen2.5:1.5b | 按需 | 986MB，Hindsight 记忆用 |
| Docker Desktop | 无容器时影响小 | 可关释放 ~600MB |
| Chrome | 常规使用 | ~500MB |

## 模型提供商对比

| 提供商 | 认证方式 | 费用 | 适合场景 |
|--------|---------|------|---------|
| **Nous Portal** (Hermes官方) | OAuth (`hermes setup --portal`) | 订阅制 | 官方推荐，300+ 模型 |
| **OpenRouter** | API Key | 按量/免费版 | 第三方聚合，有免费额度 |
| **DeepSeek 直连** | API Key | 按量 | 走官网通道 |
| **OpenRouter:free** | API Key | 免费 | 有速率限制 |

### 查找历史配置

从 session DB 查询历史 provider 配置：
```sql
SELECT s.id, s.started_at, s.model, s.billing_provider
FROM sessions s 
WHERE date(s.started_at, 'unixepoch') = '2026-05-21'
  AND s.model LIKE '%deepseek%'
ORDER BY s.started_at;
```

### 切换模型

```bash
# 查看 fallback 链
hermes fallback list

# 直接改 config.yaml (sed 方式)
sed -i '' 's/  default: old-model/  default: new-model/' ~/.hermes/config.yaml
sed -i '' 's/  provider: old-provider/  provider: new-provider/' ~/.hermes/config.yaml
```

## 快速验证

```bash
source ~/.hermes/hermes-agent/venv/bin/activate

# 验证 MPS
python3 -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}')"

# 验证 PyTorch 版本
python3 -c "import torch; print(torch.__version__)"

# 运行 YOLO 检测
python3 ~/.hermes/scripts/detect.py <图片路径>

# 运行 rembg 去背景
python3 -c "from rembg import remove; from PIL import Image; remove(Image.open('input.jpg')).save('output.png')"
```

## 参考资料

- `references/provider-fallback-test-20260531.md` — Provider fallback chain test results (2026-05-31)
- `references/session-specific.md` — 本次搭建的完整会话记录
- `references/provider-history.md` — 模型提供商切换历史
