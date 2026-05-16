# API Key 迁移指南：从 config.yaml 到 .env

把 API key 从 `config.yaml` 移到 `.env`，好处：
- **安全**：`.env` 在 `.gitignore` 里，不会被 push 到 GitHub
- **统一管理**：换 key 只改一个文件
- **绕过 GitHub 安全扫描**：config.yaml 不含明文 key，推送不会被拦

## 关键区别：两个不同的字段

| 位置 | 字段名 | 示例 |
|------|--------|------|
| `providers.<name>` | `api_key_env_var` | `api_key_env_var: GOOGLE_API_KEY` |
| `custom_providers[].` | `key_env` | `key_env: AICODEE_API_KEY` |
| `model.*` | ❌ 不支持 env var | 需要改用 `provider` 引用 |

**这是最容易被搞混的坑：标准 provider 用 `api_key_env_var`，custom_providers 用 `key_env`。** 写反了不会报错但也不会读取环境变量。

## 迁移步骤

### 1. 识别所有明文 key

config.yaml 里的 key 可能出现在三个地方：

- `model.api_key` — 主模型的 key
- `providers.<name>.api_key` — 标准 provider 的 key
- `custom_providers[].api_key` — 自定义 provider 的 key

### 2. 处理 `model` 段（关键）

如果主模型用 `provider: custom` + `model.api_key`：

```yaml
# 原来
model:
  default: MiniMax-M2.7-highspeed
  provider: custom
  base_url: https://v2.aicodee.com/v1
  api_key: YOUR_API_KEY
```

需要改成引用标准 provider + 去掉 `model` 段的 key：

```yaml
# 改后
model:
  default: MiniMax-M2.7-highspeed
  provider: aicodee          # ← 改成 providers. 段定义的 provider 名，不是 custom
```

前提是 `providers:` 下有同名 provider 配置了 base_url 和 key。

### 3. 标准 provider 改 `api_key_env_var`

```yaml
# 原来
providers:
  google:
    api_key: GOOGLE_AI_KEY_REDACTED
    base_url: https://v2.aicodee.com/v1

# 改后
providers:
  google:
    api_key_env_var: GOOGLE_API_KEY   # ← 字段名不同！
    base_url: https://v2.aicodee.com/v1
```

### 4. custom_providers 改 `key_env`

```yaml
# 原来
custom_providers:
- api_key: YOUR_API_KEY
  base_url: https://v2.aicodee.com/v1
  model: MiniMax-M2.7-highspeed
  name: V2.aicodee.com

# 改后
custom_providers:
- key_env: AICODEE_API_KEY   # ← 字段名不同！
  base_url: https://v2.aicodee.com/v1
  model: MiniMax-M2.7-highspeed
  name: V2.aicodee.com
```

### 5. 把所有 env var 加到 `.env`

```bash
# ~/.hermes/.env
GOOGLE_API_KEY=GOOGLE_AI_KEY_REDACTED
AICODEE_API_KEY=YOUR_API_KEY
NVIDIA_API_KEY=NVIDAPI_REDACTED
GROQ_API_KEY=gYOUR_API_KEY
```

`.env` 已经在 `.gitignore` 里，不会被 git 追踪。

### 6. 验证 config.yaml 已无明文 key

```bash
cd ~/.hermes && grep -E "(api_key: YOUR_API_KEY|api_key: AIza|api_key: gsk|api_key: nvapi)" config.yaml
# 如果有输出说明还有残留
```

合法的残留（不需要清理）：
- `api_key: ollama` — Ollama 不需要真实 key
- `api_key: ''` — 空字符串（auxiliary 段继承 providers）

## GitHub Secret Scanning 注意事项

1. **扫描整个 git 历史**：GitHub 的 push protection 会扫描**本次推送涉及的所有 commit**，不只是最新 commit。即使最新 commit 已清理 key，历史 commit 里还有明文 key 的话推送仍会被拦。

2. **绕过方式**：点 GitHub 返回的 unblock 链接（每个被检测到的 secret 会生成独立链接）：
   ```
   https://github.com/<owner>/<repo>/security/secret-scanning/unblock-secret/<hash>
   ```
   授权后即可 push。

3. **根治**：commit 历史里还有 key 的话，建议 squash 或 rebase 清理。最简单的做法是用 `git reset --soft` 重做一个干净 commit：
   ```bash
   git reset --soft <最后一个干净的commit的SHA>
   git add -A
   git commit -m "clean config with env var refs"
   git push --force origin main
   ```

## 内置 Provider 环境变量速查

这些是 Hermes 内置 provider 自动识别的 env var 名：

| Provider | Env Var |
|----------|---------|
| DeepSeek | `DEEPSEEK_API_KEY` |
| Google/Gemini | `GOOGLE_API_KEY` / `GEMINI_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| NVIDIA | `NVIDIA_API_KEY` |
| Groq | `GROQ_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| MiniMax | `MINIMAX_API_KEY` |
| xAI/Grok | `XAI_API_KEY` |
| GLM/Z.AI | `GLM_API_KEY` |
