# Nous Portal / hermes model OAuth 授权

## 核心限制

`hermes model` 命令需要**交互式 TTY**，通过管道/后台进程/sleep 延迟均无法绕过：

```
Error: 'hermes model' requires an interactive terminal.
It cannot be run through a pipe or non-interactive subprocess.
Run it directly in your terminal instead.
```

`--no-browser` 标志仍需要 TTY，只是跳过浏览器自动打开。

## 可行路径（已验证 2026-05-16）

**步骤 1**：用 CUA 操控 Chrome 导航到授权页
- `mcp_cua_press_key` → `cmd+L`（聚焦地址栏）
- `mcp_cua_type_text` → 填入 URL
- `mcp_cua_press_key` → `return`（回车导航）

URL 格式：
```
https://nous.aitunnel.top/auth/cli/activate?port=19797&client_id=hermes-cli
```

**步骤 2**：用户在浏览器内完成 OAuth 登录
- Google 登录、GitHub 登录，或页面上的"匿名继续"选项
- 验证码/密码输入必须本人操作，无法自动化

**步骤 3**：授权成功后 `hermes model` 后续不再需要重新授权
- `auth.json` 中 providers.nous 会自动填充

## 已知的 Chrome MCP 冲突

Chrome MCP (`mcp_chrome_*`) 在与 CUA 同时操作同一 Chrome 窗口时，容易报：
```
MCP server 'chrome' is unreachable after N consecutive failures
```

**解决**：操作 Chrome 时全程使用 CUA（`cmd+L` → `type_text` → `return`），不混用 Chrome MCP。

## Pitfalls

1. OAuth 第三方登录（Google/GitHub）无法绕过自动化限制
2. "匿名继续"选项如果存在，可跳过账号登录
3. `hermes model --no-browser` 仍需要 TTY，只是不自动开浏览器
4. 授权完成后 `auth.json` 中 nous provider 会自动写入，不需要手动编辑
