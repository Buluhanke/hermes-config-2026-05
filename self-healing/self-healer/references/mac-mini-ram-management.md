# Mac mini M4 24GB 系统资源管理

> ⚠️ **2026-06-02 更新**：Docker 生态已废弃，Colima 按需启动。

## 当前内存状态（2026-06-02 实测）

```
Colima 运行无容器：~6GB 消耗（limactl VM）
Colima stop 后：15GB used / 8.5GB free
Ollama 进程：0（已清理）
```

## 内存分配现状

| 组件 | 内存占用 | 状态 |
|------|----------|------|
| macOS + 系统服务 | ~7-8GB wired | 常驻 |
| Colima (无容器) | ~6GB | 立即停掉 |
| Chrome (9333 debug) | ~600MB | 常驻 |
| hermes-agent | ~200MB | 常驻 |
| **可用** | **~8.5GB** | — |

## Colima 内存陷阱（关键教训）

**症状**：Colima 运行但没有任何容器（`docker ps` 为空），仍消耗 ~6GB。

**发现过程**：
```
colima list → STATUS: Running, MEMORY: 6GiB
docker ps   → (空，无任何容器)
top         → PhysMem: 15G used / 8.5G free
colima stop → PhysMem: 15G used / 8.5G free  (降了 ~6GB)
```

**根因**：Colima 的 limactl VM 即使空转也保留分配的 6GB 内存。

**决策**：Colima 不跑容器时立即 `colima stop`。

## 内存检查命令

```bash
# 整体内存
top -l 1 | grep PhysMem

# 按内存排序
ps aux | sort -rn -k4 | head -10

# Colima 状态
colima list

# Ollama 残留
ps aux | grep ollama | grep -v grep

# Docker socket 是否存在（判断 Colima 是否在跑）
ls ~/.colima/default/docker.sock
```

## Ollama 模型内存对照

| 模型 | 内存占用 | 状态 |
|------|----------|------|
| qwen3-vl:latest | **15GB+** | ❌ 危险，爆掉系统 |
| qwen3-vl:2b | ~2GB | ✅ 安全 |
| qwen2.5:1.5b | ~1.5GB | ✅ 安全 |

## 清理流程

### Colima（按需）

```bash
# 查看有没有容器
docker ps

# 没有容器 → 立即停掉
colima stop

# 需要用时再启动
colima start
```

### Ollama 残留

```bash
# 检查
ps aux | grep ollama | grep -v grep

# 有则清理
pkill -9 -f ollama
```

## 当前记忆系统（不依赖 Docker）

| 组件 | 依赖 | 数据位置 |
|------|------|---------|
| MEMORY.md | 无 | ~/.hermes/memories/MEMORY.md |
| fact_store | 无（SQLite） | ~/.hermes/memory_store.db |
| session_search | 无（FTS5） | ~/.hermes/state.db |

Hindsight（Docker 版）已永久丢失，不依赖 Docker 的三层架构正常运转。
