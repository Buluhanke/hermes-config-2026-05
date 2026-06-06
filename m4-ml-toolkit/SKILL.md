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
| **ddgs** | 系统 Python | DuckDuckGo 搜索，无需 API key | ✅ 免费 |
| **playwright** | 系统 Python 3.14 | 浏览器自动化，chromium 已装 | ✅ |
| **cua** | 系统 Python 3.14 | 电脑控制（cua-driver 接口） | ✅ |
| **PaddleOCR** | 系统 Python 3.14 | ~/.paddleocr/ | ✅ |
| **EasyOCR** | 系统 Python 3.14 | — | ✅ |
| **u2net.onnx** | 手动下载 | ~/.u2net/ (168MB) | ✅ |
| **holographic** | hermes-agent 插件 | ~/.hermes/memory_store.db | ✅ 记忆系统 |

### ✅ 记忆系统现状（三层架构，不依赖 Docker）

| 组件 | 类型 | 状态 | 数据位置 |
|------|------|------|---------|
| **MEMORY.md** | 系统 prompt 快照 | ✅ 正常 | ~/.hermes/memories/MEMORY.md |
| **fact_store** | holographic 结构化记忆 | ✅ 正常，9条facts | ~/.hermes/memory_store.db |
| **session_search** | FTS5 对话检索 | ✅ 正常，9.8万条 | ~/.hermes/state.db (1.2GB) |
| **Hindsight** | 叙事化经验存储 | ❌ 永久丢失 | Docker 卷未备份 |

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

**hindsight + holographic 已全部废弃** — Docker 镜像不可恢复：
- ghcr.io/nousresearch/hindsight 访问被拒绝，docker.io 拉取超时
- ChromaDB Docker 卷数据全部丢失，无备份
- 当前记忆系统：MEMORY.md + fact_store（holographic SQLite）+ session_search（state.db FTS5）
- 三层架构完全不依赖 Docker

**停止 Colima 释放内存:**
```bash
colima stop   # 释放 VM 内存（实测降 6.5GB）
colima start  # 需要时再启动
```

### Nous Portal 模型状态变化

**背景**: 2026-05-21~22 期间，Nous Portal 的 `deepseek/deepseek-v4-flash` 免费可用。但 2026-05-31 测试时返回 404 "requires available credits"。

**教训**: 模型定价会变化，测试前不要假设收费策略与历史配置一致。

### PaddleOCR 参数已变更（2026-06-02 发现）
**旧版参数已废弃：**
```python
PaddleOCR(lang='ch', use_angle_cls=True, show_log=False)  # ❌ 报错
```
**正确写法：**
```python
PaddleOCR(lang='ch', use_textline_orientation=True, show_log=False)  # ✅
```
或直接省略（默认已启用）：
```python
PaddleOCR(lang='ch')  # ✅ 最简
```

### 截图读取失败时的备选方案（2026-06-02 发现）
browser 工具对 JS 动态加载页面（阿里云盘、1688 等）返回空。
**备选读取流程：**
1. `computer_use` capture 截图
2. `screencapture -x /tmp/page.png`
3. pytesseract 读图（hermes venv 或 Homebrew Python 均有）：
```python
from PIL import Image
import pytesseract
img = Image.open('/tmp/page.png')
text = pytesseract.image_to_string(img, lang='chi_sim+eng')
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
| hermes-agent | 常驻 | ~250MB，核心进程 |
| chromadb | 常驻 | ~300MB（原生 uvicorn） |
| colima | 按需启动 | ~50MB，轻量 VM |
| Ollama app | **用完即杀** ⚠️ | 加载模型时可达 15GB，关窗口不退出 |
| Ollama CLI (`ollama serve`) | 按需启动 ✅ | 5.7GB RSS，实测 19.7 tokens/s（M4 Metal），无 Docker |

### Ollama CLI + On-Demand Mode (实测 2026-06-05)

**安装（无 Docker，直接 brew）：**
```bash
brew install ollama          # v0.30.4
ollama serve                 # 监听 127.0.0.1:11434
```

**按需加载模式（默认开启）：**
```bash
# ~/.ollama/ollama.env
OLLAMA_FLASH_ATTENTION=1
OLLAMA_NUM_THREAD=8
OLLAMA_CONTEXT_LENGTH=8192      # 8K 够用，省 KV 缓存内存
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_KEEP_ALIVE=0             # ⭐ 推理完自动卸载模型，空闲只占 35-66MB
```

重启加载配置：`launchctl kickstart -k gui/$(id -u)/homebrew.mxcl.ollama && ollama serve &`

**启动脚本（含内存门卫）：** `~/.hermes/scripts/ollama_hermes.sh`
- 检查 `vm_stat` 的 free+inactive+speculative 页面数
- 换算成 GB：`(free_pages × 16384 / 1024^3)`
- **内存 > 7GB 才预加载模型，否则跳过**
- 服务常驻，模型按需加载/卸载

**关键坑：`vm_stat` 数字带小数点！**
```bash
# ❌ 错误（free=$3 取到带点的字符串）
free='$3'+0

# ✅ 正确（gsub 去掉点号再转数字）
gsub(/\./,"",$NF); free=$NF+0
```

**拉模型 + 自定义 Modelfile：**
```bash
ollama pull llama3.1:8b                    # 自动选 Q4_K_M，4.9GB
ollama create hermes-8b -f ~/Modelfile.hermes8b
```

**实测内存（2026-06-05）：**
| 状态 | Ollama RSS |
|------|-----------|
| 服务空闲（模型已卸载） | **35-66 MB** |
| 模型加载中（llama3.1:8b Q4_K_M） | **5.7 GB** |
| Hermes Gateway | ~405 MB |
| Mac mini M4 空闲（加载后） | ~16 GB |

> ⭐ 按需模式让 Ollama 平时零内存开销，只有推理时才加载 5.7GB，推理完自动卸载。

**启动脚本已固化路径：** `~/.hermes/scripts/ollama_hermes.sh`

| qwen3-vl:2b / qwen2.5 | 按需 | 卸载后不占内存 |
| Docker 容器 | 不使用 | 已废弃，改用原生方案 |

> ⚠️ SKILL.md 旧版提到 Hermes Docker 内存限制 — **已废弃**，无 Docker，直接跑在 `~/.hermes/hermes-agent/venv` 里。Ollama 也用 native brew 安装，KEEP_ALIVE=0 按需加载模型。

### 内存管理清单

**安装（无 Docker，直接 brew）：**
```bash
brew install ollama          # v0.30.4
ollama serve                 # 监听 127.0.0.1:11434
```

**按需加载模式（默认开启）：**
```bash
# ~/.ollama/ollama.env
OLLAMA_FLASH_ATTENTION=1
OLLAMA_NUM_THREAD=8
OLLAMA_CONTEXT_LENGTH=8192      # 8K 够用，省 KV 缓存内存
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_KEEP_ALIVE=0             # ⭐ 推理完自动卸载模型，空闲只占 35-66MB
```

重启加载配置：`launchctl kickstart -k gui/$(id -u)/homebrew.mxcl.ollama && ollama serve &`

**启动脚本（含内存门卫）：** `~/.hermes/scripts/ollama_hermes.sh`
- 检查 `vm_stat` 的 free+inactive+speculative 页面数
- 换算成 GB：`(free_pages × 16384 / 1024^3)`
- **内存 > 7GB 才预加载模型，否则跳过**
- 服务常驻，模型按需加载/卸载

**关键坑：`vm_stat` 数字带小数点！**
```bash
# ❌ 错误（free=$3 取到带点的字符串）
free='$3'+0

# ✅ 正确（gsub 去掉点号再转数字）
gsub(/\./,"",$NF); free=$NF+0
```

**拉模型 + 自定义 Modelfile：**
```bash
ollama pull llama3.1:8b                    # 自动选 Q4_K_M，4.9GB
ollama create hermes-8b -f ~/Modelfile.hermes8b
```

**实测内存（2026-06-05）：**
| 状态 | Ollama RSS |
|------|-----------|
| 服务空闲（模型已卸载） | **35-66 MB** |
| 模型加载中（llama3.1:8b Q4_K_M） | **5.7 GB** |
| Hermes Gateway | ~405 MB |
| Mac mini M4 空闲（加载后） | ~16 GB |

> ⭐ 按需模式让 Ollama 平时零内存开销，只有推理时才加载 5.7GB，推理完自动卸载。

### Ollama CLI 安装与启动（实测 2026-06-05）

**无 Docker，直接装命令行版：**
```bash
brew install ollama          # v0.30.4 已安装
ollama serve                 # 后台运行，监听 127.0.0.1:11434
```

**启动脚本（带省内存配置）：**
```bash
~/.hermes/scripts/ollama_hermes.sh      # 一键启动 + 验证
```

**拉模型（Ollama 自动选量化）：**
```bash
ollama pull llama3.1:8b        # 默认 Q4_K_M 量化，磁盘 4.9GB
ollama list                    # 查看已下载模型
```

**生成自定义省内存模型：**
```bash
ollama create hermes-8b -f ~/Modelfile.hermes8b
```

**Hermes 对接地址（非 Docker，直接连 Ollama）：**
```yaml
# ~/.hermes/config.yaml
model:
  default: hermes-8b
  base_url: http://127.0.0.1:11434/v1
  api_key: ollama
```

**内存实测（2026-06-05）：**
| 组件 | 状态 | RSS |
|------|------|-----|
| Ollama 服务空闲（KEEP_ALIVE=0，模型已卸载） | 空闲 | **35-66 MB** |
| Ollama 模型加载中（llama3.1:8b Q4_K_M） | 加载 | **~5.7 GB** |
| Hermes Gateway（原生 venv，无 Docker） | 常驻 | **~405 MB** |
| Mac mini M4 空闲（模型已卸载） | — | **~16 GB** |

> ⚠️ SKILL.md 旧版提到 Hermes Docker 内存限制 — **已废弃**，无 Docker，直接跑在 `~/.hermes/hermes-agent/venv` 里。
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
- `references/dl-setup-20260531.md` — Deep learning setup (PyTorch + transformers + MPS verification)
- `references/ollama-8b-m4-24gb-20260605.md` — Ollama 8B Q4_K_M on Mac mini M4: env vars, Modelfile, Hermes Docker memory cap, 24GB budget table. Cross-validated across DeepSeek + Grok + Doubao.

## 参考资料

- `references/system-state-20260601.md` — 当前系统能力快照（2026-06-01）
- `references/provider-fallback-test-20260531.md` — Provider fallback chain test results (2026-05-31)
- `references/session-specific.md` — 本次搭建的完整会话记录
- `references/provider-history.md` — 模型提供商切换历史
