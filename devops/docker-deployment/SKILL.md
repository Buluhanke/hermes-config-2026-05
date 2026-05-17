# Docker容器化部署

## 1. 为什么用Docker

### 环境一致性
- 开发、测试、生产环境完全一致
- 消除"在我机器上能运行"的问题
- 依赖版本统一管理

### 资源隔离
- 每个服务独立运行环境
- 避免端口冲突和依赖冲突
- 进程级别隔离，更安全

### 快速部署
- 秒级启动新容器
- 轻松扩缩容
- 一键回滚到历史版本

---

## 2. 基础概念

### 镜像 (Image)
- 容器运行的只读模板
- 由多层文件系统叠加组成
- 示例：`nginx:alpine`, `python:3.11-slim`

### 容器 (Container)
- 镜像的运行实例
- 可写层在最上层
- 容器间相互隔离

### Dockerfile
- 构建镜像的脚本文件
- 定义基础镜像、依赖安装、配置、启动命令
- 示例指令：`FROM`, `RUN`, `COPY`, `CMD`, `EXPOSE`, `ENV`

### Docker Compose
- 定义多容器应用
- YAML配置所有服务、网络、数据卷
- 一键启动完整应用栈

---

## 3. Hermes服务Docker化示例

### Dockerfile
```dockerfile
# 基础镜像 - 使用ARM64兼容的Alpine
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "-m", "hermes"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  hermes:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hermes-agent
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=info
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    # Mac Mini M4资源限制
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 1G
    networks:
      - hermes-network

  # 可选：Redis缓存
  redis:
    image: redis:alpine
    container_name: hermes-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - hermes-network

networks:
  hermes-network:
    driver: bridge

volumes:
  redis-data:
```

---

## 4. 常用命令

### 构建镜像
```bash
# 从Dockerfile构建
docker build -t hermes:latest .

# 带标签构建
docker build -t hermes:latest -t hermes:v1.0.0 .

# 构建并指定平台（ARM64）
docker build --platform linux/arm64 -t hermes:arm64 .
```

### 运行容器
```bash
# 前台运行
docker run hermes:latest

# 后台运行
docker run -d --name hermes hermes:latest

# 带端口映射和环境变量
docker run -d -p 8000:8000 -e PYTHONUNBUFFERED=1 hermes:latest

# 挂载数据卷
docker run -d -v $(pwd)/data:/app/data hermes:latest
```

### 容器管理
```bash
# 列出运行中的容器
docker ps

# 列出所有容器（包括停止的）
docker ps -a

# 查看容器详细信息
docker inspect hermes

# 停止/启动容器
docker stop hermes
docker start hermes

# 重启容器
docker restart hermes

# 删除容器
docker rm hermes
docker rm -f hermes  # 强制删除运行中的容器
```

### 日志查看
```bash
# 查看实时日志
docker logs -f hermes

# 查看最近100行日志
docker logs --tail 100 hermes

# 查看时间戳
docker logs -t hermes

# 过滤错误日志
docker logs hermes 2>&1 | grep ERROR
```

### 进入容器
```bash
# 进入容器bash
docker exec -it hermes /bin/bash

# 进入容器sh（轻量级）
docker exec -it hermes /bin/sh

# 以root用户进入
docker exec -u root -it hermes /bin/bash

# 执行单条命令
docker exec hermes python -c "import hermes; print(hermes.__version__)"
```

### Compose命令
```bash
# 启动所有服务
docker-compose up -d

# 重新构建并启动
docker-compose up -d --build

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 镜像管理
```bash
# 列出本地镜像
docker images

# 删除镜像
docker rmi hermes:latest

# 清理悬空镜像
docker image prune

# 清理所有未使用镜像
docker image prune -a
```

---

## 5. Mac Mini M4注意事项

### ARM64镜像
```bash
# 确保使用ARM64兼容镜像
docker pull python:3.11-slim  # 自动获取ARM64版本

# 构建时指定平台
docker build --platform linux/arm64 -t hermes:arm64 .

# 查看镜像架构
docker inspect python:3.11-slim | grep Architecture
```

### 资源分配
```yaml
# docker-compose.yml 中资源配置
deploy:
  resources:
    limits:
      cpus: '2'        # Mac Mini M4性能核数量
      memory: 4G       # 根据实际内存调整
    reservations:
      cpus: '1'
      memory: 1G
```

建议：
- M4 Pro/Max：可分配更多资源（4-8核，8-16G）
- M4基础版：建议限制在2-4核，2-4G内存
- 避免内存超额导致系统不稳定

### 存储清理
```bash
# 查看磁盘使用
docker system df

# 清理未使用资源
docker system prune

# 清理包括：
# - 停止的容器
# - 未使用的网络
# - 悬空镜像
# - 构建缓存

# 完全清理（谨慎使用）
docker system prune -a --volumes

# 定期清理（建议加入定时任务）
# 每月执行一次
docker image prune -a
docker builder prune -a
```

### 性能优化
```bash
# 启用Macvlan网络（提升网络性能）
# 在docker-compose.yml中配置

# 使用精简基础镜像
FROM python:3.11-slim  # 比 alpine 兼容性更好

# 多阶段构建减小镜像体积
# 生产环境使用distroless或scratch
```

### 常见问题
```bash
# 问题：容器内中文显示乱码
# 解决：设置环境变量
environment:
  - LANG=C.UTF-8
  - LC_ALL=C.UTF-8

# 问题：端口已被占用
# 解决：修改宿主机端口映射
ports:
  - "8001:8000"  # 改用8001

# 问题：容器启动失败
# 解决：查看日志排查
docker logs hermes
docker-compose logs hermes
```