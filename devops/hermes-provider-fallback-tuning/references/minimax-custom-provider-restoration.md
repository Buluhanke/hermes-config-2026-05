# MiniMax-M3 自定义代理服务 Provider 恢复指南

## 问题场景 (2026-07-05 修正版)

用户删除了自定义代理 `123.56.67.77:9100` (MiniMax M3)，然后又要求加回 fallback 链。

## 根因分析

`custom:xxx` provider 需要三处同步恢复，缺一不可：

1. `.env` — API key 环境变量
2. `custom_providers:` 下的命名条目
3. `fallback_providers[]` 下的 fallback 条目

**注意**：之前 2026-07-04 记录说要用 `provider: openrouter` 代替 `custom:xxx`，这是**错误诊断**。
正确的修复是恢复 `custom_providers` 的 YAML 结构，而不是改 provider 类型。

## 恢复步骤

### 1. 添加 API key 到 .env

```bash
echo 'export MINIMAX_M3_API_KEY="sk-your-key-here"' >> ~/.hermes/.env
```

或者用 `hermes config set`（推荐，不受第一行空格问题影响）：
```bash
hermes config set MINIMAX_M3_API_KEY "sk-your-key-here"
```

### 2. 恢复 custom_providers 条目

`custom_providers:` 块在 config.yaml 中需要**命名条目**，每个条目有 `base_url` 和 `key_env`：

```bash
sed -i '' '/^custom_providers:/a\\
  "123.56.67.77:9100":\\
    base_url: http://123.56.67.77:9100/v1\\
    key_env: MINIMAX_M3_API_KEY
' ~/.hermes/config.yaml
```

**正确格式**：
```yaml
custom_providers:
  "123.56.67.77:9100":        # ← 命名条目，必须与 provider: 后的名称一致
    base_url: http://123.56.67.77:9100/v1
    key_env: MINIMAX_M3_API_KEY   # ← 变量名（不含$）
```

**错误格式**（会导致 "Unknown provider"）：
```yaml
custom_providers:
    api_key: sk-cp-..._P-U    # ← 裸值、无命名、无 key_env
```

### 3. 恢复 fallback_providers 条目

在 Agnes Flash 条目前面插入：
```bash
sed -i '' '/^  - api_key: ${AGNES_API_KEY}/i\\
  - api_key: ${MINIMAX_M3_API_KEY}\\
    base_url: http://123.56.67.77:9100/v1\\
    label: MiniMax M3 (123.56.67.77:9100 代理)\\
    model: MiniMax-M3\\
    provider: custom:123.56.67.77:9100\\
    request_timeout_seconds: 20
' ~/.hermes/config.yaml
```

注意 model 名称**大小写敏感**——必须与 `/v1/models` 返回的完全一致（`MiniMax-M3` 不是 `minimax-m3`）。

### 4. 验证连通性

```bash
# 测试 API key + 端点
source ~/.hermes/.env 2>/dev/null || true
KEY=$(awk -F= '/^MINIMAX_M3_API_KEY=/{print $2; exit}' ~/.hermes/.env | tr -d '\\r\\n"')
curl -s -w "\\nHTTP:%{http_code}" http://123.56.67.77:9100/v1/chat/completions \\
  -H "Authorization: Bearer $KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"MiniMax-M3","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
# 期望: HTTP:200（或有余额提示，但非 401/403）
```

### 5. 重启 gateway

```bash
hermes gateway restart
```

## 删除时的 checklist（逆向操作）

删除 custom provider 必须检查**两处**：

```bash
# 1. 找所有出现位置
grep -n '123.56.67.77\\|MiniMax M3' ~/.hermes/config.yaml

# 2. 从 fallback_providers[] 删除整个条目
# 找到条目的起始行号 L，看完整条目到几行
sed -i '' 'L,+5d' ~/.hermes/config.yaml

# 3. 从 custom_providers[] 删除命名条目
sed -i '' '/^  "123.56.67.77:9100":/,/^    key_env:/d' ~/.hermes/config.yaml

# 4. 确认干净
grep -n '123.56.67.77\\|MiniMax M3' ~/.hermes/config.yaml || echo "All clean"
```

## 2026-07-05 补充: 模型切换与快捷别名

### 模型从 M3 改为 M2.7-highspeed

同一端点的模型可以切换。用户最初用 `MiniMax-M3`，后改为 `MiniMax-M2.7-highspeed`。
两种模型都在 `/v1/models` 列表里。切换步骤：

```bash
# 1. 查可用模型
curl -s http://123.56.67.77:9100/v1/models -H "Authorization: Bearer $KEY"

# 2. 修改 config.yaml 的 model 字段（注意大小写）
sed -i '' 's/model: MiniMax-M3/model: MiniMax-M2.7-highspeed/' ~/.hermes/config.yaml
```

### 常搭配快捷别名一起设置

加完 fallback 条目后，用户通常会要快捷切换指令：

```bash
hermes config set model.aliases.mini "custom:123.56.67.77:9100/MiniMax-M2.7-highspeed"
hermes config set model.aliases.deep "deepseek/deepseek-v4-flash"
hermes config set model.aliases.fb "deepseek/deepseek-v4-flash"
```

然后在 chat 里 `/model mini` 秒切。

### 阿里云代理余额不足的典型返回值

```json
{"error":{"message":"预扣费额度失败, 用户剩余额度: ＄0.200000, 需要预扣费额度: ＄0.300000","code":"insufficient_user_quota"}}
```

这个是 403，不是 401/500 —— key 有效，余额不够。告诉用户充钱或用免费模型（如该代理上的 `MiniMax-M2.5` 或 `MiniMax-M2.7-highspeed`）。

## 常见错误

| 错误 | 现象 | 修复 |
|---|---|---|
| `.env` 有 key 但 `custom_providers` 缺失 | "Unknown provider 'custom:xxx'" | 补充 `custom_providers` 条目 |
| `custom_providers` 格式错误（裸 api_key） | "Unknown provider 'custom:xxx'" | 改为命名条目 + `key_env` |
| 模型名大小写错误 | "model_not_found" | 从 `/v1/models` 复制 exact ID |
| key 有但余额不足 | "insufficient_user_quota" (403) | 充钱或用免费模型 |
| ⛔ 错误改成 `provider: openrouter` | 能走但路由不对 | 改回 `provider: custom:xxx` |

## 关联参考

- `SKILL.md` — Model aliases section (快捷切换指令), Fallback chain ordering section (排序策略)
- `provider-env-mapping.md` — 完整 provider 与 env var 映射表