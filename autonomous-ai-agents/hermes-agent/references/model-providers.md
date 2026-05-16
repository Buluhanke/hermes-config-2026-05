# 模型 Provider 配置参考

## 已知 Key 格式

| Provider | Key 格式 | 示例 |
|---|---|---|
| aicodee (OpenAI兼容) | `YOUR_API_KEY...` / `YOUR_API_KEY-` 开头 | `YOUR_API_KEY-RfbDpBXANQ3TzdA0W0Fb...` |
| MiniMax 直连 | 通常不是 `YOUR_API_KEY` 开头，错误码 `2049` 表示 key 无效 | - |

## .env 文件写入
- `.env` 是受保护文件，`patch` 工具会拒绝写入
- 正确方式：用 `echo -e` 追加内容，需用户审批

## 直连 vs 中转判断
- 直连失败时看错误信息：`invalid api key (2049)` = key 格式不对，不是中转 key
- `login fail` = key 未配置或格式错误
