# Web Dashboard 使用参考

## 启动命令

```bash
# 本地访问（默认 127.0.0.1）
hermes dashboard --port 3847 --no-open

# 局域网访问（需先配置 basic_auth，见下方）
hermes dashboard --port 3847 --host 0.0.0.0 --no-open
```

**注意：`hermes web` 是错的，正确是 `hermes dashboard`**

## 局域网认证配置（必须）

Dashboard 拒绝绑定 0.0.0.0 除非配置了 basic_auth，否则报错：
```
Refusing to bind dashboard to 0.0.0.0 — the auth gate engages on non-loopback binds,
but no auth providers are registered.
```

**步骤：**

1. 生成 scrypt hash（必须在 hermes-agent venv 里运行）：
```bash
cd ~/.hermes/hermes-agent && python3 -c "
import sys; sys.path.insert(0, '.')
from plugins.dashboard_auth.basic import hash_password
print(hash_password('你的密码'))
"
# 输出：scrypt$16384$8$1$<salt>$<hash>
```

2. 编辑 config.yaml（用 Python yaml 模块）：
```bash
python3 -c "
import yaml
with open('/Users/aimac/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
cfg['dashboard']['basic_auth']['username'] = 'hermes'
cfg['dashboard']['basic_auth']['password'] = ''
cfg['dashboard']['basic_auth']['password_hash'] = 'scrypt\$16384\$8\$1\$<salt>\$<hash>'
with open('/Users/aimac/.hermes/config.yaml', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
"
```

3. 重启 dashboard：
```bash
pkill -f 'hermes dashboard'
hermes dashboard --port 3847 --host 0.0.0.0 --no-open &
```

4. 局域网访问：`http://<Mac-mini-IP>:3847`，输入用户名密码登录

> ⚠️ **不能用 pbkdf2** — dashboard 认证用的是 scrypt，格式必须匹配 `scrypt$16384$8$1$<salt>$<hash>`。生成 hash 必须在 hermes-agent venv 里运行，否则 import 会失败。

## 功能模块

| 模块 | 说明 |
|------|------|
| Status | agent 版本、活跃 session、gateway 状态、已连接平台 |
| Config editor | schema 驱动表单，支持 import/export/reset |
| API Keys | 设置/清除/掩码查看，分组管理 |
| Sessions | 会话管理 |
| Skills | 技能管理 |
| Cron | 定时任务 |
| Logs | 日志查看 |
| Analytics | 分析面板 |

## 已知问题

- v0.15.0 dashboard 有无限循环 bug → **v0.15.1 已修复**
- 端口默认 9119，当前会话用 3847 避免冲突
- `browser_navigate` 无法访问 localhost URL（内部限制）→ 用 `open http://localhost:3847` 从终端打开

## 进程管理

```bash
# 查看是否在跑
lsof -i :3847

# 杀掉重启
pkill -f "hermes dashboard"
hermes dashboard --port 3847 --no-open &
```
