# Hermes 大体检参考标准（2026-05-27 → 2026-06-06 更新）

## 体检维度清单（完整版，2026-06-06 更新）

### 第1步：系统大盘
```python
import psutil, os
mem = psutil.virtual_memory()
swap = psutil.swap_memory()
load = os.getloadavg()
disk = psutil.disk_usage('/')
```
阈值：内存 >80% 告警；Swap >50% 黄色预警；磁盘可用 <10% 告警

### 第2步：核心模块
```bash
pgrep -f 'hermes_cli.main gateway'
pgrep -f 'hermes_cli.main dashboard'
curl -s http://127.0.0.1:9333/json/version
lsof -iTCP -sTCP:LISTEN -P -n | head -30
```
注意：CDP `/json` 返回 0 tabs 正常，只要 `/json/version` 有响应

### 第3步：Config 检查
```bash
wc -l ~/.hermes/.env
grep -n 'model:' ~/.hermes/config.yaml | head -20
```
问题模式：`${VAR}` 引用无法解析、config 硬编码 API key、fallback_chain 引用不存在 provider

### 第4步：平台连接
```bash
lsof -iTCP -sTCP:LISTEN -P -n | grep -E '8642|49853|9210|4001|4301|4310|11434|9333'
```

### 第5步：脚本/技能清理检查
```bash
ls ~/.hermes/scripts/ | grep -E 'test_|\.bak|_v1|_v2'
du -sh ~/.hermes/scripts/
ls ~/.hermes/skills/ | wc -l  # 目标 30-40
```

### 第6步：日志分析
```bash
du -sh ~/.hermes/logs/* | sort -rh | head -20
wc -l ~/.hermes/logs/errors.log
ls ~/.hermes/logs/*.gz 2>/dev/null
find ~/.hermes/logs/ -name '*.log' -empty
```

### 第7步：内存大户进程
```bash
ps aux --sort=-%mem | head -12
```
典型大户：Chrome(多进程)、Ollama(RSS 73MB+ VSZ 400GB+)、Electron(200-800MB)、Gateway+Dashboard(各 200-400MB)

### 第8步：Cronjobs 检查
```bash
ls ~/.hermes/cron/*.json 2>/dev/null
```

### 第9步：Swap 深度分析
```bash
sysctl vm.swapusage
vm_stat
```
优化：清理 Ollama 模型、重启系统、减少 Electron 应用。Swap 是历史记录，当前内存压力低可不管
