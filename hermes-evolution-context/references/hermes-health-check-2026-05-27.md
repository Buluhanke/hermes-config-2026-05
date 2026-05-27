# Hermes 大体检参考标准（2026-05-27）

## 体检维度清单

### 1. Config 版本
```bash
grep "_config_version" ~/.hermes/config.yaml
# 期望：24（最新版）
```

### 2. Gateway 进程存活
```bash
ps aux | grep -i "hermes.*gateway" | grep -v grep
# 期望：有进程在跑
```

### 3. screen_watch hook（主动屏幕感知）
检查 `~/.hermes/logs/gateway_restart*.log` 里有没有：
```
[hooks] Loaded hook 'screen_watch'
[screen_watch] 已启动屏幕监控
```
如果只有 `[screen_watch] 跳过（缺少humanization_core）` → gateway venv 缺依赖（见 heremes-humanization-core SKILL.md）

### 4. humanization_core 在 gateway venv 里能导入
```bash
cd ~/.hermes/hermes-agent
.venv/bin/python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/hermes-humanization-core'))
from humanization_core import capture_screen, ask_vlm
print('ok')
"
# 期望：[humanization] 人机控制权监听已启动 → ok
```

### 5. Gateway 重启后端口冲突检测
重启后看日志有没有 `already in use (PID ...)`：
- 有 → 旧进程没杀干净，用 `kill -9 <pid>` 强制杀
- 无 → 正常启动

### 6. Ollama VLM 模型状态
```bash
curl -s http://127.0.0.1:11434/api/tags | python3 -c "import json,sys; mods=json.load(sys.stdin)['models'];print([m['name'] for m in mods])"
```
screen_watch 需要 `qwen2.5vl:7b` 或 `ahmadwaqar/smolvlm2-agentic-gui:latest`

### 7. Cron jobs 状态
```bash
hermes cron list 2>/dev/null || ~/.hermes/hermes-agent/.venv/bin/python3 -m hermes_cli.main cron list
```

## 本次体检发现的故障等级

| 故障 | 等级 | 修复命令 |
|------|------|---------|
| gateway venv 缺 humanization_core 依赖 | 🔴 重大 | `.venv/bin/python3 -m pip install pyautogui numpy mss pynput` |
| Config 版本 v23 | ⚠️ 维护 | `sed -i '' 's/_config_version: 23/_config_version: 24/' ~/.hermes/config.yaml` |
| Gateway 重启后旧进程残留 | ⚠️ 维护 | `kill -9 <pid>` |