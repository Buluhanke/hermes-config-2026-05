# Nous Portal + DeepSeek V4 Flash 配置（2026-05-16）

## 背景
DeepSeek V4 Flash 免费路线：通过 Nous Portal（OAuth 登录），不走 DeepSeek 官方 API。
auth.json 里 `providers: {}` 表示尚未授权。

## 操作方法
在 Mac 终端手动运行：
```bash
hermes model
```
然后：
1. 选 Nous Portal
2. 浏览器自动弹出授权页面
3. 登录/授权 OAuth
4. 回来选 DeepSeek V4 Flash

## macOS Terminal 自动化限制

### 实测失败的 osascript 方式
```python
# ❌ 超时
osascript -e 'tell application "Terminal" to do script "hermes model"'

# ❌ 超时
subprocess.run(["osascript", "/tmp/open_hermes.scpt"])
```

### 正确做法
创建 `.command` 文件，手动双击运行：
```bash
cat > /tmp/hermes_model.command << 'EOF'
#!/bin/bash
cd /Users/aimac
/Users/aimac/.hermes/hermes-agent/venv/bin/hermes model
EOF
chmod +x /tmp/hermes_model.command
```

## OpenHuman 不是 API 服务
OpenHuman（tinyhumansai/openhuman）是 **Tauri 桌面应用**，无 HTTP API，无法被 Hermes 调用。**结论：不安装。**
