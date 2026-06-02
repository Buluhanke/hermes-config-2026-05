# GitHub Repo Deployment: Microsoft Fara-7B Case Study

实战记录：用户要求"安装试试"微软 Fara-7B AI助手项目。

---

## 实际执行流程

```bash
# 1. Clone（无 proxy，HTTPS 成功）
git clone https://github.com/microsoft/fara.git
# → 成功，无需代理

# 2. uv sync 安装
cd ~/fara
uv sync
# → fara 0.1.0 安装成功，playwright/openai/pillow/tenacity/pyyaml/jsonschema 等依赖全部装好

# 3. 检查运行需求
cat README.md | grep -A5 "Quick Start\|Requirements"
# → 需要 vllm >= 0.10.0 + NVIDIA GPU（FP16 需要 14GB VRAM）

# 4. 现状
# - vllm 未安装
# - Mac 是 Apple Silicon，无 NVIDIA GPU
# → Fara 已安装但无法运行
```

---

## 关键教训

| 阶段 | 教训 |
|------|------|
| **Clone** | HTTPS 直接成功，不需要 proxy |
| **uv sync** | 成功率高，输出清晰 |
| **post-install** | Playwright 项目需要 `playwright install` 单独安装浏览器 |
| **运行依赖** | 大模型项目需要 GPU，Mac 上没有 NVIDIA → 无法运行 |

---

## 判断"能不能跑"的三层检查

```
1. uv sync 成功？
   └── Yes → Python 依赖满足
       └── README 要求 vllm / NVIDIA GPU？
           └── Yes → 当前 Mac 不满足，标记"安装成功但运行受阻"
           └── No → 尝试运行
```

---

## 快速上手命令（标准模板）

```bash
git clone https://github.com/OWNER/REPO.git
cd REPO
uv sync 2>&1 | tail -20          # 观察成功/失败信号
ls .venv/bin/ | head -10          # 确认 venv 存在
.venv/bin/python --version        # 确认 Python
cat README.md | grep -A3 "install\|requirement\|quickstart"
```

## 失败模式记录

| 错误 | 原因 | 解法 |
|------|------|------|
| `vllm` 导入失败 | vllm 未装或无 GPU | pip install vllm（有 NVIDIA GPU 时） |
| `playwright` 浏览器找不到 | 未运行 `playwright install` | `playwright install` |
| `curl: (7) Failed to connect` | 网络问题，尝试 proxy | `curl -x http://127.0.0.1:7897 ...` |