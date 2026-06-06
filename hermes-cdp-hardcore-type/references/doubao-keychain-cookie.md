# 豆包/字节系登录态迁移失败根因（2026-06-04）

## 问题描述
从用户前台Chrome（`~/Library/Application Support/Google/Chrome/Default/`）复制Cookies到debug profile后，豆包等字节跳动系网站session cookie的`value`字段为空，`encrypted_value`非空。复制无效，换设备=退出登录。

## 根因：OS X Keychain主密钥加密

Chrome（macOS）对以下字节系域名使用**OS X Keychain 主密钥**加密cookie：
- `*.doubao.com`
- `*.bytedance.com`
- `*.toutiao.com`
- `*.feishu.cn`（部分）

加密密钥绑定到Chrome实例身份（每个Chrome.app启动时生成独立Keychain身份），复制cookie文件到另一个profile后，新Chrome实例无法用自己的Keychain解密别人的加密值。

## 验证方法

```bash
# 查看doubao.com cookie的加密状态
sqlite3 ~/.hermes/chrome-debug/Default/Cookies \
  "SELECT host_key, name, value, length(encrypted_value) as enc_len \
   FROM cookies WHERE host_key LIKE '%doubao%';"

# 预期：value='' 且 encrypted_value 非空（enc_len > 0）→ Keychain加密，复制无效
```

## 为什么Session Storage也救不回来

- `Session Storage/000003.log`（LevelDB）中存在doubao.com的session信息（`namespace-...-https://www.doubao.com/`、`__tea_session_id`字段）
- 但豆包/抖音的Token设计是**设备UUID级**：服务端根据设备指纹生成session，换设备需要重新认证
- Session Storage能恢复部分上下文，但不足以骗过服务端的风控

## 登录方式（判断用哪种方式迁移）

豆包/抖音系常见登录方式：
- **手机号+验证码**（最常见，字节系标配）
- **抖音App扫码登录**（抖音App内扫码）
- **Google/Apple账号联合登录**（少数）

如果用户是手机号登录，在debug Chrome重新登录一次即可（推荐）。

## 解法

| 方案 | 可靠性 | 操作 |
|------|--------|------|
| 在debug Chrome重新登录一次 | ⭐⭐⭐⭐⭐ | 手动登录，cookies明文写入 |
| 用真实Chrome.app启动debug profile | ⭐⭐⭐ | 真实Chrome用自己的Keychain解密自己的cookie |
| 复制Session Storage文件 | ⭐ | ByteDance可能检查设备签名，未验证 |
| Playwright操作用户Chrome | ⭐⭐ | 需要用户Chrome开启debug端口，CDP直连已登录会话 |

## 预防

如果任务依赖"保持豆包登录态"，不要尝试cookie文件复制。直接在debug Chrome中完成一次登录，cookies写入后即为明文。