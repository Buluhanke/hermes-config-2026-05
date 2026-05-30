# Mac mini M4 24GB 系统资源管理

## 内存困境（24GB Mac mini）

```
当前消耗（2026-05-31实测）：
  macOS + 系统服务          ~8GB wired
  Docker Linux VM           ~9GB wired（始终保留，不可压缩）
  Chrome (9333调试端口)      ~600MB
  飞书 + QQ                  ~1GB
  Hermes agent               ~200MB
  ─────────────────────────────────
  总计                       ~19GB wired

剩余可用                    ~5GB

风险：Ollama qwen3-vl:2b模型  15GB → 系统爆掉，123MB剩余，卡死
```

**关键矛盾**：Docker Linux VM占用~9GB wired内存（macOS Virtualization.framework），无法回收，必须始终保留。即使关闭Docker Desktop UI，backend和VM进程仍在运行。

## 内存检查命令

```bash
# 整体内存状态
top -l 1 | grep PhysMem
# 输出：PhysMem: 5180M used (2129M wired, 753M compressor), 18G unused.

# 按CPU排序（找出消耗最高的进程）
ps aux | sort -rn -k3 | head -10

# 按内存排序（找出内存大户）
ps aux | sort -rn -k4 | head -10

# Docker Linux VM进程（消耗~9GB）
ps aux | grep 'Virtualization.VirtualMachine' | grep -v grep

# Ollama runner进程（可能占用15GB+）
ps aux | grep 'ollama runner' | grep -v grep
```

## Ollama模型内存对照表

| 模型 | 内存占用 | 状态 |
|------|----------|------|
| qwen3-vl:latest (6.1GB) | **15GB+ (含推理buffer)，实测系统从22GB→5GB used** | ❌ 危险，24GB机型会导致系统卡死 |
| qwen3-vl:2b | ~6GB | ⚠️ 可用但接近上限 |
| qwen2.5:1.5b | ~2-3GB | ✅ 安全 |
| nomic-embed-text | ~500MB | ✅ 安全 |

**经验**：qwen3-vl:latest在Mac mini M4 24GB上会压垮系统。

## 清理流程

### Step 1: 识别资源大户
```bash
# 列出所有占用>1GB内存的进程
ps aux | sort -rn -k4 | awk '$5 > 1000000 {print $5/1024/1024 "MB", $11, $12, $13}'

# 按CPU排序（找CPU大户）
ps aux | sort -rn -k3 | head -10

# 查macOS内存信息（wired vs compressor）
top -l 1 | grep PhysMem
# 输出：PhysMem: 5180M used (2129M wired, 753M compressor), 18G unused.
```

### Step 2: 安全清理名单（可kill不影响Hermes核心功能）

| 进程 | 风险 | 清理方式 |
|------|------|----------|
| WeatherWidget | 无 | `kill <PID>` |
| Doubao Browser | 无 | `pkill -f Doubao` |
| Docker Desktop | 无（backend和VM仍在） | `pkill -f 'Docker Desktop'` |
| Ollama runner | 有（失去本地VLM） | `pkill -f 'ollama runner'` |

### Step 3: 清理Ollama的正确方式（防止自动重启）
```bash
# 只kill runner不行，ollama serve会立即拉起新runner
# 必须完全停止ollama服务：pkill -f不够（有shell script自动拉起），用pkill -9
pkill -9 -f 'ollama'  # 杀所有ollama进程（包括自动重启的shell wrapper）

# 或者通过defaults关闭自动启动
defaults write com.ollama OLLAMA_AUTO_START false 2>/dev/null || true

# 验证：确认所有ollama进程消失
ps aux | grep -i ollama | grep -v grep || echo "ollama stopped"
```
# 或者在ollama应用内先停止服务
osascript -e 'tell app "Ollama" to quit'
```

### Step 4: 验证清理结果
```bash
sleep 1 && top -l 1 | grep PhysMem
```

## Docker容器与Hermes服务的依赖关系

| 容器 | 端口 | Hermes依赖 | 关闭影响 |
|------|------|------------|----------|
| hermes-hindsight | 8899 | ✅ 长期记忆 | 记忆查询失效 |
| hermes-ai-n8n-1 | 5678 | ✅ 工作流自动化 | n8n工作流失效 |
| hermes-ai-chromadb-1 | 8000 | ✅ 向量数据库 | RAG/搜索失效 |
| searxng | 8888 | ✅ 搜索聚合 | web搜索失效 |
| open-webui | 3000 | ✅ AI对话界面 | OpenWebUI不可用 |
| (Ollama) | 11434 | ❌ 独立服务 | 可用Docker版替代 |

**关闭Docker = 关闭所有上述服务**。只有需要这些服务时才开Docker。

## 建议配置（24GB Mac mini）

### 方案A：保留Docker（需要Ollama API）
- 不运行Ollama.app（内存15GB太大）
- 改用Docker内open-webui通过11434端口调用Ollama（模型在容器内）
- 只跑轻量级容器：n8n、hindsight、searxng
- 不要同时跑Docker Linux VM + Ollama本地模型

### 方案B：完全不用Docker
- 卸载Docker Desktop（同时关闭Linux VM，释放9GB）
- Ollama.app可以跑小模型（qwen2.5:1.5b）
- 用AirGPT或其他方式提供LLM API
- 代价：失去n8n/hindsight/chromadb/searxng

### 方案C：均衡（推荐）
- Docker继续跑（上述5个容器）
- 不装Ollama.app，改用open-webui里的Ollama
- 不用qwen3-vl:latest，改用qwen3-vl:2b或更小的