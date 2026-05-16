# Dashboard / Web UI 模型切换操作流程

## 前置条件

**自定义 Provider 必须同时出现在 `providers:` 和 `custom_providers:` 两个段**，否则 Dashboard 的模型选择器里看不到该 provider 的模型。

```yaml
# ✅ 正确：同时配置两个段
custom_providers:
- name: V2.aicodee.com
  base_url: https://v2.aicodee.com/v1
  api_key: YOUR_API_KEY
  model: MiniMax-M2.7-highspeed

providers:
  aicodee:
    api_key: YOUR_API_KEY
    base_url: https://v2.aicodee.com/v1
```

- `custom_providers` 的 `name`（如 `V2.aicodee.com`）和 `providers` 的键名（如 `aicodee`）**不需要一致**
- Dashboard 显示时取 `providers` 段的键名
- 模型列表来自 `custom_providers` 段配置的模型

## 操作步骤

1. 打开 Dashboard：浏览器访问 `http://localhost:5173`（dev）或 `http://localhost:9119`（production build）
2. 左侧导航栏点击 **MODELS**
3. 在 "MODEL SETTINGS" 区域的 "MAIN MODEL" 右侧，点击 **CHANGE** 按钮
4. 弹出 "SET MAIN MODEL" 对话框，显示所有 provider 及其模型数
5. 点击目标 provider（如 `aicodee`）展开模型列表
6. 点击目标模型（如 `MiniMax-M2.7-highspeed`）选中它
7. 底部点击 **SWITCH** 确认切换
8. 对话框关闭，"MAIN MODEL" 显示变为新的 provider/model

## 效果

- Dashboard 的切换**直接修改 `config.yaml`** 的 `model.default` 和 `model.provider` 字段
- 对所有**新会话**生效，正在进行的会话不受影响
- 与 `/model` 命令不同：`/model` 是会话级临时切换，Dashboard 是配置级永久切换

## 与 `/model` 命令的对比

| 特性 | Dashboard (CHANGE) | `/model <provider>/<model>` |
|------|-------------------|---------------------------|
| 生效范围 | 全局限定（config.yaml） | 当前会话临时 |
| 是否持久 | 是（写 config.yaml） | 否（仅当前 session） |
| 重启后是否保留 | 是 | 否 |
| 需要 Gateway 服务 | 是 | 是 |
| 新会话默认模型 | 新的 model.config | 不变（回到 config.yaml 默认） |

## 常见问题

### Dashboard 模型下拉列表显示很多我不认识的模型

**现象**：在 Dashboard 的模型选择器里看到十几个 MiniMax/Groq 变体，但 `config.yaml` 里只配了一个 MiniMax。

**原因**：Dashboard 的模型选择器**同时从两个来源拉取**模型列表：
1. **config.yaml 的 `providers:` + `custom_providers:`** — 你实际配置的条目
2. **模型目录（model_catalog）** — 从远程 URL 自动拉取，列出该 provider 下所有可用模型

你看到的"多个 MiniMax"（MiniMax-M2.7-highspeed、MiniMax-M2.5 等）是模型目录自动发现的，不是配置里有多个。

**解决**：如果只想显示特定模型，在 `model_catalog.providers` 下配置白名单：
```yaml
model_catalog:
  providers:
    aicodee:
      models: [MiniMax-M2.7-highspeed]
```
或者直接忽略——目录里的额外选项不影响使用。

### ⚠️ Dashboard 有两种模型切换方式，fallback 行为不同

Dashboard 存在两种不同的模型切换入口，fallback 覆盖行为完全不同：

| 入口 | 位置 | 效果 | fallback_model 生效？ |
|------|------|------|----------------------|
| **CHANGE 按钮** | MODELS → MAIN MODEL → CHANGE | 写 `config.yaml`，配置级永久切换 | ✅ 是 |
| **会话下拉框** | Chat 页面顶部模型指示器旁的切换 | 会话级临时覆盖，不写 config | ❌ 否（跳过 fallback） |

**会话级下拉框跳过 fallback 的后果**：如果在该下拉框切换到一个余额用尽的模型（如 MiniMax-M2.7-highspeed 已 403），Dashboard Chat 会直接静默失败，不会自动回退到 fallback_model。这时 QQ/微信等其他渠道不受影响（它们用 config.yaml 里的主模型）。

**推荐做法**：在 Dashboard 切换模型测试时，始终用 **MODELS 页面的 CHANGE 按钮**。Chat 页面的临时下拉框仅用于快速查看，不要依赖它的故障保护。

### Dashboard 点 CHANGE 没有我配的 provider

**原因**：provider 只配在 `custom_providers` 段，没有在 `providers` 段添加同名条目。Dashboard 模型选择器只读取 `providers` 段的 provider。

**解决**：在 `config.yaml` 的 `providers:` 下添加该 provider，然后重启 gateway。

### 点 SWITCH 后没反应

**原因**：Dashboard 后端未运行或 session token 过期。

**解决**：
```bash
# 检查后端是否在跑
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119
# 如果返回 000（连接不上），启动后端
~/.hermes/hermes-agent/venv/bin/hermes dashboard --host 127.0.0.1 --port 9119 &
```

### 切完后新会话还是旧模型

**原因**：config.yaml 中可能还存在 `model.default` 的旧值，或 `custom_providers` 的优先级问题。也有可能是 `HERMES_MODEL` 环境变量覆盖。

**排查**：
```bash
grep HERMES_MODEL ~/.hermes/config.yaml ~/.hermes/.env
```
如果存在，注释掉即可。
