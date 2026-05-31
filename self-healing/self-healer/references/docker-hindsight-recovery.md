# Docker Hub 网络阻断与 Hindsight 恢复流程

## 网络诊断命令

```bash
# Docker Hub 完全阻断（100%丢包）
curl -s --max-time 10 https://registry-1.docker.io/v2/ -o /dev/null && echo "docker.io:ok" || echo "docker.io:blocked"

# ghcr.io 状态
curl -s --max-time 10 https://ghcr.io/v2/ -o /dev/null && echo "ghcr.io:ok" || echo "ghcr.io:blocked"
```

## 当前网络状态（2026-06-02 实测）

| 域名 | 状态 | 说明 |
|------|------|------|
| `registry-1.docker.io` | ❌ 100% 丢包 | Docker Hub 主站，完全阻断 |
| `docker.io` | ❌ 超时 | Docker Hub 备用域名，同样阻断 |
| `ghcr.io` | ✅ 可通 | GitHub Container Registry，ping OK |

## Docker Hub 阻断时的容器恢复流程

### Step 1：检查 Colima 和 Docker 状态

```bash
colima list
docker ps -a
```

### Step 2：优先用原生替代方案

**ChromaDB** 有 pip 包，可以原生运行：

```bash
cd ~/.hermes/hermes-agent
./venv/bin/pip install chromadb opentelemetry-instrumentation-fastapi -i https://pypi.tuna.tsinghua.edu.cn/simple
./venv/bin/python -c "from chromadb.app import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)" &
sleep 2
curl -s http://localhost:8000/api/v2/heartbeat
```

### Step 3：Hindsight 没有 pip 包，只能等网络恢复

```bash
# 检查镜像层是否已部分下载
docker images

# 清理残留层
docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null

# 尝试从 ghcr.io 拉取（如果镜像在 ghcr.io）
docker pull ghcr.io/vectorize-io/hindsight:latest

# 或尝试镜像加速
docker pull docker.1ms.run/ghcr.io/vectorize-io/hindsight:latest
```

### Step 4：Hindsight 容器启动

```bash
docker run -d \
  --name hermes-hindsight \
  -p 8899:8000 \
  -v ~/.hindsight/data:/data \
  ghcr.io/vectorize-io/hindsight:latest

# 验证
curl -s http://localhost:8899/health
```

## 凌晨重试 Cron 任务建议

如需设凌晨重试，在 Docker Hub 恢复后自动拉取：

```
docker pull ghcr.io/vectorize-io/hindsight:latest && docker start hermes-hindsight
```

## 关联文档

- `references/api-key-centralization.md` — API Key 集中化管理流程（含 key 状态总表）
- `references/mac-mini-ram-management.md` — Colima vs Docker Desktop 选型，内存控制
