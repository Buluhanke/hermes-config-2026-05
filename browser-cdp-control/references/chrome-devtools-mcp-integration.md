# chrome-devtools-mcp 集成记录

## 基本信息
- **包名**: chrome-devtools-mcp
- **版本**: v1.2.0
- **Stars**: 43.9K (GitHub ChromeDevTools/chrome-devtools-mcp)
- **许可证**: Apache-2.0
- **安装**: `npx -y chrome-devtools-mcp@latest`
- **配置**: `~/.hermes/config.yaml` → `mcp_servers.chrome-devtools-mcp`

## 配置
```yaml
chrome-devtools-mcp:
  args:
  - -y
  - chrome-devtools-mcp@latest
  - --browserUrl=http://127.0.0.1:9222
  command: npx
  enabled: true
  timeout: 120
```

**关键**: `--browserUrl=http://127.0.0.1:9222` 直接接 Hermes 现有 Chrome，11 个 AI 网站登录态直接可用。

## 29 个工具
click, close_page, drag, emulate, evaluate_script, fill, fill_form, get_console_message, get_network_request, handle_dialog, hover, lighthouse_audit, list_console_messages, list_network_requests, list_pages, navigate_page, new_page, performance_analyze_insight, performance_start_trace, performance_stop_trace, press_key, resize_page, select_page, take_heapsnapshot, take_screenshot, take_snapshot, type_text, upload_file, wait_for

## 实测验证
- `hermes mcp test chrome-devtools-mcp` → Connected (1878ms), 29 tools discovered
- Chrome 版本: 149.0.7827.155
- CDP 端口: 9222
- 登录态: chrome-profile-mirror (11 个 AI 站)

## 与现有工具关系
- **不替换** CDP Runtime.evaluate（互补）
- **不冲突** cua-driver（cua-driver 管 macOS 原生，chrome-devtools-mcp 管 Web）
- **不冲突** agent-browser（agent-browser 是 CLI，chrome-devtools-mcp 是 MCP toolset）
