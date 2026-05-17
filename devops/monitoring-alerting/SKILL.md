# 监控告警体系 (Monitoring & Alerting)

## 概述

Hermes Agent 监控告警体系覆盖系统层、应用层、业务层三个维度,确保服务稳定运行.

## 监控目标

### 系统层监控
- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络连通性

### 应用层监控
- Hermes服务进程存活状态
- Hermes服务健康状态

### 业务层监控
- 1688询价任务执行状态
- 1688 Cookie有效性
- 1688网站可访问性

## 监控工具栈

| 类别 | 工具 | 说明 |
|------|------|------|
| 系统监控 | `top` / `htop` / `macOS Activity Monitor` | 系统资源实时监控 |
| 指标采集 | Prometheus + node_exporter | 时序指标采集存储 |
| 可视化 | Grafana | 监控仪表盘 |
| 告警触发 | n8n | 工作流自动化告警 |
| 通知渠道 | 邮件 / QQ / 短信 | 告警消息推送 |

## Hermes健康检测脚本

```bash
#!/bin/bash
# hermes-health-check.sh
# 用法: ./hermes-health-check.sh

set -e

LOG_FILE="${HERMES_LOG_DIR:-~/.hermes/logs}/health-$(date +%Y%m%d).log"
ALERT_SCRIPT="$HOME/.hermes/skills/devops/monitoring-alerting/alert.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local severity="$1"
    local message="$2"
    if [ -x "$ALERT_SCRIPT" ]; then
        "$ALERT_SCRIPT" "$severity" "$message"
    else
        log "ALERT [$severity]: $message"
    fi
}

# ============================================
# 1. 检查Hermes进程是否存活
# ============================================
log "检查Hermes进程状态..."
if pgrep -f "hermes-agent" > /dev/null 2>&1; then
    log "Hermes进程运行正常"
else
    log "Hermes进程不存在，尝试重启..."
    send_alert "critical" "Hermes进程消失，正在尝试重启"
    hermes dashboard &
    sleep 5
    if pgrep -f "hermes-agent" > /dev/null 2>&1; then
        log "Hermes进程重启成功"
        send_alert "info" "Hermes进程已自动恢复"
    else
        log "Hermes进程重启失败"
        send_alert "critical" "Hermes进程重启失败，需要人工介入"
    fi
fi

# ============================================
# 2. 检查1688网站可访问性
# ============================================
log "检查1688网站连通性..."
FAILED=0
for i in 1 2 3; do
    if curl -s --max-time 10 -o /dev/null -w "%{http_code}" https://www.1688.com | grep -q "200\|302\|301"; then
        log "1688网站访问正常 (尝试 $i/3)"
        FAILED=0
        break
    else
        log "1688网站访问失败 (尝试 $i/3)"
        FAILED=$((FAILED + 1))
        sleep 2
    fi
done

if [ $FAILED -ge 3 ]; then
    log "1688网站连续3次访问失败"
    send_alert "warning" "1688网站无法访问，已失败 $FAILED 次"
fi

# ============================================
# 3. 检查磁盘空间
# ============================================
log "检查磁盘空间..."
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log "磁盘空间不足: ${DISK_USAGE}%"
    send_alert "critical" "磁盘使用率 ${DISK_USAGE}%，超过90%阈值"
elif [ "$DISK_USAGE" -gt 80 ]; then
    log "磁盘空间警告: ${DISK_USAGE}%"
    send_alert "warning" "磁盘使用率 ${DISK_USAGE}%，超过80%阈值"
else
    log "磁盘空间正常: ${DISK_USAGE}%"
fi

# ============================================
# 4. 检查内存使用率
# ============================================
log "检查内存使用率..."
MEMORY_USAGE=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
TOTAL_PAGES=$(sysctl -n hw.pagesize)
ACTIVE_PAGES=$((MEMORY_USAGE))
TOTAL_MEMORY=$(sysctl -n hw.memsize)
ACTIVE_MEMORY=$((ACTIVE_PAGES * TOTAL_PAGES))
MEMORY_PERCENT=$((ACTIVE_MEMORY * 100 / TOTAL_MEMORY))

if [ "$MEMORY_PERCENT" -gt 85 ]; then
    log "内存使用率过高: ${MEMORY_PERCENT}%"
    send_alert "warning" "内存使用率 ${MEMORY_PERCENT}%，超过85%阈值"
else
    log "内存使用率正常: ${MEMORY_PERCENT}%"
fi

# ============================================
# 5. 检查CPU使用率 (5分钟平均)
# ============================================
log "检查CPU使用率..."
CPU_USAGE=$(top -l 1 -n 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
if [ ! -z "$CPU_USAGE" ]; then
    log "CPU使用率: ${CPU_USAGE}%"
fi

log "健康检测完成"
```

## 告警阈值配置

```yaml
# monitoring-thresholds.yaml

thresholds:
  cpu:
    warning: 80    # 百分比
    critical: 90
    duration: 300  # 持续秒数
    
  memory:
    warning: 85
    critical: 95
    duration: 300
    
  disk:
    warning: 80
    critical: 90
    duration: 0    # 立即告警
    
  network:
    timeout: 10    # 连接超时秒数
    retries: 3      # 重试次数
    
  hermes:
    check_interval: 60   # 检查间隔秒数
    restart_on_fail: true
    max_restarts: 3      # 最大重启次数
    
 1688:
    check_interval: 300  # 5分钟检查一次
    retries: 3
    alert_on_failure: true
```

## Prometheus监控配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'hermes'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: /metrics
    
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
```

```yaml
# alert_rules.yml
groups:
  - name: hermes_alerts
    interval: 30s
    rules:
      - alert: HermesProcessDown
        expr: up{job="hermes"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Hermes进程已停止"
          description: "Hermes服务已经停止运行超过1分钟"
          
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率已超过80%持续5分钟"
          
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率已超过85%持续5分钟"
          
      - alert: HighDiskUsage
        expr: (node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"} * 100 > 90
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足"
          description: "磁盘使用率已超过90%"
```

## n8n集成配置

### Webhook接收配置

```
n8n Webhook URL: http://localhost:5678/webhook/prometheus-alerts
```

### 告警工作流设计

1. **接收层**: Prometheus AlertManager → n8n Webhook
2. **处理层**: n8n Workflow解析告警内容
3. **通知层**: 路由到对应通知渠道

```javascript
// n8n Workflow - 告警路由
const alert = $json;
const severity = alert.labels.severity;
const message = `${alert.annotations.summary}: ${alert.annotations.description}`;

const notifications = {
  critical: ['email', 'qq', 'sms'],
  warning: ['email', 'qq'],
  info: ['qq']
};

const channels = notifications[severity] || notifications.info;

for (const channel of channels) {
  // 根据渠道发送通知
  if (channel === 'email') {
    // 发送邮件
  } else if (channel === 'qq') {
    // 发送QQ消息
  } else if (channel === 'sms') {
    // 发送短信
  }
}
```

## Cron定时任务配置

```bash
# 添加到 crontab: crontab -e

# 每小时执行一次健康检测
0 * * * * $HOME/.hermes/skills/devops/monitoring-alerting/hermes-health-check.sh >> $HOME/.hermes/logs/health-cron.log 2>&1

# 每5分钟检查Hermes进程
*/5 * * * * pgrep -f "hermes-agent" > /dev/null || (hermes dashboard &)

# 每分钟检查1688连通性
* * * * * curl -s --max-time 5 -o /dev/null -w "%{http_code}" https://www.1688.com | grep -v "200\|302\|301" && echo "$(date) 1688访问失败" >> $HOME/.hermes/logs/1688-fail.log
```

## Grafana仪表盘

### 关键面板

1. **系统概览**
   - CPU使用率 (实时 + 历史趋势)
   - 内存使用率
   - 磁盘使用率
   - 网络IO

2. **Hermes服务状态**
   - 进程存活状态
   - 响应时间
   - 任务队列长度

3. **业务监控**
   - 1688询价任务成功率
   - 任务执行时间
   - 异常任务统计

### 导入仪表盘

```bash
# Grafana仪表盘导入
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @hermes-dashboard.json
```

## 通知模板

### 邮件告警模板

```
主题: [{{ severity }}] Hermes监控系统告警

您好,

检测到以下告警:

告警级别: {{ severity }}
告警名称: {{ alert_name }}
告警描述: {{ description }}
发生时间: {{ start_time }}
持续时间: {{ duration }}

当前状态: {{ status }}

请及时处理。

此邮件由Hermes监控系统自动发送
```

### QQ消息模板

```
[Hermes监控告警]
级别: {{ severity }}
告警: {{ alert_name }}
描述: {{ description }}
时间: {{ start_time }}
状态: {{ status }}
```

## 快速开始

### 1. 启动基础监控服务

```bash
# 启动Prometheus
prometheus --config.file=~/.hermes/skills/devops/monitoring-alerting/prometheus.yml

# 启动Grafana
grafana-server -homepath /usr/local/opt/grafana/share/grafana

# 启动node_exporter
node_exporter --collector.textfile.directory=/tmp
```

### 2. 验证监控状态

```bash
# 检查Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq

# 检查Grafana
open http://localhost:3000

# 手动执行健康检测
~/.hermes/skills/devops/monitoring-alerting/hermes-health-check.sh
```

### 3. 配置n8n工作流

1. 打开 n8n: http://localhost:5678
2. 创建新Workflow
3. 添加Webhook节点 (接收Prometheus告警)
4. 添加条件分支 (根据severity路由)
5. 添加通知节点 (邮件/QQ/短信)

## 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 告警未触发 | Prometheus规则错误 | 检查alert_rules.yml语法 |
| n8n未收到告警 | Webhook配置错误 | 验证AlertManager配置 |
| Hermes进程反复崩溃 | 内存不足/代码bug | 查看hermes日志 |
| 1688访问失败 | 网络问题/Cookie过期 | 检查网络/更新Cookie |

## 相关文档

- [Prometheus官方文档](https://prometheus.io/docs/)
- [Grafana官方文档](https://grafana.com/docs/)
- [n8n官方文档](https://docs.n8n.io/)
- [Hermes Agent文档](./../../README.md)