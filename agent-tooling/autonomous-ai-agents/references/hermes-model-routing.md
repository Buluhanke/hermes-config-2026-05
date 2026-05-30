# Hermes 模型路由配置

## 三层路由（当前配置）

```
Primary:   deepseek/deepseek-v4-flash  (via custom) → v2.aicodee.com 中转
Fallback 1: MiniMax-M2.7               (via minimax-cn)
Fallback 2: deepseek/deepseek-v4-flash  (via deepseek) → api.deepseek.com 直连
```

配置命令：
```bash
hermes config set model.provider custom
hermes config set model.base_url "https://v2.aicodee.com/v1"
hermes config set model.default "deepseek/deepseek-v4-flash"
```

Python直接写入（hermes config命令有时会把list序列化为string）：
```python
import yaml
with open('/Users/aimac/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
cfg['fallback_providers'] = [
    {'provider': 'minimax-cn', 'model': 'MiniMax-M2.7'},
    {'provider': 'deepseek', 'model': 'deepseek/deepseek-v4-flash', 'base_url': 'https://api.deepseek.com'}
]
with open('/Users/aimac/.hermes/config.yaml', 'w') as f:
    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
```

查看：
```bash
hermes fallback list
```

## 关键概念区分

### 故障切换（Hermes fallback链）
- **触发条件**：API报错、5xx、超时、rate-limit
- **用途**：主渠道挂了切到备用渠道
- **不适用**：额度用完

### 额度触发切换
- **触发条件**：额度/配额用完（需要中转平台支持）
- **实现位置**：v2.aicodee.com 平台的智能路由配置
- **Hermes层无法控制**：Hermes fallback是故障触发，不是额度触发

## v2.aicodee.com 定位

- **性质**：自托管Docker聚合工具（非托管服务）
- **功能**：多渠道聚合 + 智能路由策略配置
- **额度管理**：需在 v2.aicodee.com 后台配置多渠道轮询/故障转移
- **部署**：Docker一键部署，开箱即用

## 额度自动切换正确路径

若需要 MiniMax 额度用完 → 自动切 DeepSeek，有两个方案：

### 方案A（推荐）：在 v2.aicodee.com 配置智能路由
在部署的 v2.aicodee.com 实例里配置多渠道 + 路由策略，让平台自己判断额度消耗

### 方案B：写监控脚本
写一个脚本轮询 MiniMax API 额度剩余量，接近用完时改 config.yaml 切渠道

**现状**：用户倾向方案简单，暂未决定