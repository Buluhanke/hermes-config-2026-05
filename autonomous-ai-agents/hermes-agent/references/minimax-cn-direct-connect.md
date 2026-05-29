# minimax-cn 直连配置 (2026-05-29)

## Overview

minimax-cn 是 MiniMax 国内节点，绕过 aicodee 代理，直连 `api.minimaxi.com`。

## 前提条件

`.env` 里已有正确配置：
```bash
MINIMAX_CN_API_KEY=***
MINIMAX_CN_BASE_URL=https://api.minimaxi.com/anthropic
```

## 切换命令

```bash
hermes config set model.provider minimax-cn
hermes config set model.default MiniMax-M2.7
```

## 验证

```bash
hermes config show | grep -E "provider|default"
# 应显示：provider: minimax-cn, default: MiniMax-M2.7
```

## 效果

- **当前会话**：重开新会话生效
- **下次新会话**：自动用 minimax-cn + MiniMax-M2.7

## 判断标准

| Provider | 适用场景 |
|----------|---------|
| minimax-cn | 国内节点，延迟低，适合国内业务 |
| aicodee-relay | 走代理，可能有额度/速度优势 |

## 注意事项

- 切换后 `aicodee-relay` 不受影响，只是默认 provider 变了
- 如果 aicodee 有独特模型（不在 minimax-cn 目录里的），仍可通过 `/model aicodee/模型名` 临时切换