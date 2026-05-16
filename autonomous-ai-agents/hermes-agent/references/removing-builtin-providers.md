# 删除 Hermes 内置 Provider 的完整触碰点

Hermes 内置 provider（如 MiniMax）的配置不仅存在于 `config.yaml`，还在源码中硬编码。要彻底删除，需清理以下 **6 个层面**。

## 1. config.yaml — 用户配置层

```yaml
# 删除 custom_providers 中的相关条目
custom_providers: []

# 清空 model 段的 default 和 fallback（如果指向该 provider）
model:
  default: ''
  fallback: ''
```

## 2. CANONICAL_PROVIDERS — 模型选择器列表

文件: `hermes_cli/models.py`

删除 `CANONICAL_PROVIDERS` 列表中的对应 `ProviderEntry(...)` 条目。模型选择器（TUI 和 Dashboard）基于此列表显示"未配置的"供应商选项。

## 3. _PROVIDER_MODELS — 静态模型列表

文件: `hermes_cli/models.py`

删除 `_PROVIDER_MODELS` 字典中的对应键值对（`"minimax": [...]`）。控制 `hermes model` 命令显示的模型列表。

## 4. PROVIDER_REGISTRY — Provider 注册中心

文件: `hermes_cli/auth.py`

删除 `PROVIDER_REGISTRY` 字典中的 `ProviderConfig(...)` 条目。这是提供商的身份认证配置（API key 环境变量名、OAuth 流程、base URL 等）。

## 5. 插件目录 — 模型实现代码

目录: `plugins/model-providers/<name>/`

直接删除整个插件目录（含 `__init__.py` 和 `plugin.yaml`）。

## 6. 副作用清理

清理引用该 provider 的其他文件：

| 文件 | 需清理内容 |
|------|-----------|
| `hermes_cli/status.py` | OAuth 状态显示、import 语句 |
| `hermes_cli/doctor.py` | 健康检查条目、name_to_canonical 映射 |
| `hermes_cli/auth_commands.py` | OAuth 登录流程分支、_OAUTH_CAPABLE_PROVIDERS 集合 |
| `hermes_cli/main.py` | 模型选择流程分支、通用 provider 集合 |
| `cli.py` | CLI 帮助文本中的 provider 列表 |
| `trajectory_compressor.py` | URL host 到 provider 的映射 |

## 注意事项

- 源码修改会被 `git pull` 或 `hermes update` 覆盖，需记录改动以便升级后重做
- 修改后需重启 gateway/TUI 才能生效：
  ```bash
  pkill -f "hermes.*gateway"  # 或 lsof -i :8642 找到 PID 后 kill
  ```
- 测试文件（`tests/test_minimax_oauth.py` 等）是功能无关的，不会影响生产运行
