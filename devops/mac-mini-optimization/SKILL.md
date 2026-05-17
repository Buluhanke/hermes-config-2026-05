# Mac Mini M4 24G 统一内存深度优化

## 核心内容

### 内存优化
```bash
# 查看内存使用
top -l 1 | head -10

# Hermess进程优先级设置（降低不必要的内存占用）
# 建议限制并发模型数量，避免内存溢出
```

### 模型运行策略
- Qwen2.5-VL-7B：需要约8G显存，建议单实例
- UI-TARS：轻量，专用于GUI定位，优先使用
- 内存分配：留4G给系统和其他应用

### 并发控制
```python
# 限制同时运行的VLM推理数量
MAX_CONCURRENT_VLM = 1

# 使用队列串行化请求
import queue
vlm_request_queue = queue.Queue()
```

### 存储优化
- Docker镜像定期清理
- 浏览器缓存限制（Chrome profile限制在2G以内）
- 日志文件轮转（logrotate）

### 性能监控
```bash
# 实时监控CPU/内存
alias hermes-stats='top -l 1 | grep -E "Hermes|CPU|PhysMem"'

# 磁盘空间警告
df -h | awk '$5 > 80 {print "警告: " $1 " 使用率 " $5}'
```

### 推荐配置
- Docker Desktop：4核CPU + 6G内存
- Chrome：单Tab + 扩展限制在20个以内
- Ollama：最多同时运行1个模型
- 预留：4G给系统 + 2G给其他临时需求