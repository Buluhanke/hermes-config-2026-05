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
ML 运行环境:  ~/.hermes/hermes-agent/venv (Python 3.11, 注意: 是 venv 不是 .venv)
GPU 加速:     MPS (Metal Performance Shaders) ✅
```

激活命令: `source ~/.hermes/hermes-agent/venv/bin/activate`（不是 `.venv`）

## 已安装的工具链

| 工具 | 安装命令 | 模型缓存位置 | 状态 |
|------|---------|-------------|------|
| **PyTorch 2.12** | venv 自带 | — | ✅ MPS可用 |
| **torchvision 0.27** | venv 自带 | — | ✅ |
| **transformers** | venv 自带 | ~/.cache/huggingface/ | ✅ |
| **YOLOv8** | venv 自带 | 当前目录 | ✅ 170ms |
| **PaddleOCR** | 系统 Python 3.14 | ~/.paddleocr/ | ✅ |
| **EasyOCR** | 系统 Python 3.14 | — | ✅ |
| **u2net.onnx** | 手动下载 | ~/.u2net/ (168MB) | ✅ |
| **holographic** | hermes-agent 插件 | ~/.hermes/memory_store.db | ✅ 记忆系统 |

### ✅ 记忆系统现状

**已切换到 holographic**（原生 Python 插件，不依赖 Docker）：
- 数据库：`~/.hermes/memory_store.db`
- 工具：`fact_store add` / `fact_store list`
- chromadb：原生 uvicorn 端口 8000（heartbeat 正常）

## 已知问题

### 🔥 Ollama App 关窗口不退出（内存杀手）

**症状**: Ollama app 窗口关闭后，`ollama serve` 进程继续运行，加载模型时 RSS 可达 15GB。

**根因**: Ollama Electron app 默认"关窗口不退出服务"。

**清理步骤（实测有效）:**
```bash
# 1. 先杀 Electron 守护父进程
kill -9 $(ps aux | grep 'ollama' | grep -v grep | awk 'NR==1 {print $2}')

# 2. 再杀 ollama serve 和 runner
pkill -9 -f ollama

# 验证
ps aux | grep ollama | grep -v grep  # 应无输出
```

**设置开机不自动启动:**
```bash
defaults write com.ollama.ollama OLLAMA_AUTO_START -bool false
```
注意：这只阻止开机自启，**不阻止 app 关闭后服务继续运行**。

**彻底解决方案（选一个）:**
1. 卸载 Ollama app — 最干净
2. 改用命令行版 `ollama serve`（不装 app）— 按需启动
3. 保留 app + 用完手动 `pkill -9 -f ollama`

**实测内存:** 杀后 23GB 机器空闲从 96MB → 17GB。

### Docker/Colima 内存占用

**实际使用 Colima（非 Docker Desktop）**，VM 本身占 ~50MB，比 Docker Desktop 的 4.8GB 轻量很多。

**完全释放 Docker 内存:**
```bash
colima stop   # 释放 VM 内存
colima start  # 需要时再启动
```

**hindsight 已废弃** — 已切换到 holographic（原生 Python 插件，不依赖 Docker）。
当前记忆系统：holographic（memory_store.db）+ chromadb（原生 uvicorn 端口 8000）。

**停止后实测：** Colima stop 后 23GB 机器空闲从 237MB → 8GB。

### Nous Portal 模型状态变化

**背景**: 2026-05-21~22 期间，Nous Portal 的 `deepseek/deepseek-v4-flash` 免费可用。但 2026-05-31 测试时返回 404 "requires available credits"。

**教训**: 模型定价会变化，测试前不要假设收费策略与历史配置一致。

### 包安装到不同 Python 环境

`uv pip install` 默认装到 venv (Python 3.11)，而系统 `python3` 是 3.14。
```bash
source ~/.hermes/hermes-agent/venv/bin/activate   # 先激活再装
```

## 内存管理清单

M4 Mac 24GB 内存分配建议：

| 进程 | 建议状态 | 说明 |
|------|---------|------|
| hermes-agent | 常驻 | ~250MB，核心进程 |
| chromadb | 常驻 | ~300MB（原生 uvicorn） |
| colima | 按需启动 | ~50MB，轻量 VM |
| Ollama app | **用完即杀** ⚠️ | 加载模型时可达 15GB，关窗口不退出 |
| qwen3-vl:2b / qwen2.5 | 按需 | 卸载后不占内存 |
| Docker 容器 | 不使用 | 已废弃，改用原生方案 |

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
