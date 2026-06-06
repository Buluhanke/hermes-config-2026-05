# Hermes 大体检参考标准（2026-05-27 → 2026-06-06 更新）

## 体检维度清单（完整版，2026-06-06 更新）

### 第1步：系统大盘
```python
# 用 execute_code 一次性采集，不要分多次 terminal
import psutil, subprocess, os
mem = psutil.virtual_memory()        # 内存压力
swap = psutil.swap_memory()          # swap 使用率（>50% = 之前内存爆过）
load = os.getloadavg()               # CPU 负载
disk = psutil.disk_usage('/')        # 磁盘空间
```

**阈值**：
- 内存 >80% → 红色告警
- Swap >50% → 黄色预警（系统曾内存不足）
- 磁盘可用 <10% → 红色告警

### 第2步：核心模块
```bash
# Gateway
pgrep -f 'hermes_cli.main gateway' | head -1
# Dashboard
pgrep -f 'hermes_cli.main dashboard' | head -1
# CDP Chrome
curl -s http://127.0.0.1:9333/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'Browser' in d else 'FAIL')"
# 监听端口
lsof -iTCP -sTCP:LISTEN -P -n | head -30
```

**注意**：Chrome CDP 可能返回 `/json` 为 0 tabs（无 tab 注册）——正常，只要 `/json/version` 有响应就是 CDP 可用。

### 第3步：Config 检查
```bash
# 检查 .env 存在性和 key
wc -l ~/.hermes/.env
grep -c '=' ~/.hermes/.env  # 有效 KV 对数量
# 检查 config.yaml 大小
wc -l ~/.hermes/config.yaml
# 检查 model 字段（用户规则：不应写死）
grep -n 'model:' ~/.hermes/config.yaml | head -20
```

**已知问题模式**：
- `fallback_providers` 中 `${VAR}` 引用无法解析 → 需要检查 `.env` 是否被 gateway 进程加载
- config.yaml 中写死了 API key（`sk-xxx` / `nvapi-xxx`）→ 用户规则说不该写死
- `fallback_chain` 引用了不存在的 provider name → 查 `custom_providers` 是否注册了同名 provider

### 第4步：平台连接
```bash
# 看端口对应平台
# 8642=API Server, 49853=Doubao, 9210/4001/4301/4310=QQ, 11434=Ollama, 9333=Chrome
lsof -iTCP -sTCP:LISTEN -P -n | grep -E '8642|49853|9210|4001|4301|4310|11434|9333'
```

### 第5步：脚本/技能清理检查
```bash
# Scripts 目录
ls ~/.hermes/scripts/ | wc -l
ls ~/.hermes/scripts/ | grep -E 'test_|\.bak|_v1|_v2'  # 冗余文件
du -sh ~/.hermes/scripts/
# 技能目录
ls ~/.hermes/skills/ | wc -l  # 目标 30-40，超了告警
# 找 0KB 空目录
for d in ~/.hermes/skills/*/; do size=$(du -sk "$d" | cut -f1); if [ "$size" = "0" ]; then echo "$d 空目录"; fi; done
```

### 第6步：日志分析
```bash
# 各日志大小
du -sh ~/.hermes/logs/* | sort -rh | head -20
# 错误统计
wc -l ~/.hermes/logs/errors.log
# 最近错误
tail -20 ~/.hermes/logs/errors.log
# 检查 .gz 旧归档
ls ~/.hermes/logs/*.gz 2>/dev/null
# 检查空日志文件
find ~/.hermes/logs/ -name '*.log' -empty
```

### 第7步：内存大户进程
```bash
# top 10 内存
ps aux --sort=-%mem | head -12
# top 10 RSS
ps aux --sort=-%mem | awk 'NR>1{print $2, $4, int($6/1024), $11}' | sort -k2 -rn | head -10
```

**典型内存大户**：
- Chrome (多进程，每个子进程 100-500MB)
- Ollama (RSS 通常 73MB+，但 VSZ 可能 400GB+)
- Claude/Doubao/Electron 应用 (200-800MB)
- Python gateway + dashboard (各 200-400MB)

### 第8步：Cronjobs 检查
```bash
ls ~/.hermes/cron/*.json 2>/dev/null
# 每个 job 的 schedule
for f in ~/.hermes/cron/*.json; do echo "$f: $(python3 -c 'import json; print(json.load(open("$f")).get("schedule","N/A"))' 2>/dev/null)"; done
```

### 第9步：Swap 分析（深度）
```bash
# 系统 swap
sysctl vm.swapusage
# vm_stat 详情
vm_stat
# 看哪些进程 swap 最多
top -l 1 -n 0 -o SWAP  # macOS
```

**Swap 优化方法**：
- 清理 Ollama 模型：`ollama rm <model>`
- 重启系统（最直接）
- 减少 Electron 应用数
- 注意：swap 是历史记录，不是实时占用；如果当前内存压力低，swap 不用管

## 修复操作清单（按优先级）

### 🔴 高风险（影响功能）
1. Fallback 模型不可用 → 检查 provider 注册 + 环境变量
2. CDP Chrome 无响应 → 检查端口 + 重启 Chrome
3. Gateway/Dashboard 未运行 → 重启

### 🟡 中风险（影响性能/维护）
1. Scripts 目录冗余（>100 文件）→ 清理旧版/bak/test 文件
2. 空壳技能目录 → 删除
3. 日志膨胀（>30MB）→ 清理 .gz + empty + old reports
4. Swap >50% → 评估 Ollama 模型/重启

### 🟢 低风险（可选优化）
1. 清理 __pycache__ (~270MB) — 可能破坏依赖，谨慎
2. venv 大小 3.3G — 不碰
3. .git 目录 (24MB) — 不动

## 跳过项（按用户规则）
- 不动模型配置（model/fallback_chain/api_key）
- 不动通讯渠道配置（QQBot/Telegram/Weixin 等适配层）
