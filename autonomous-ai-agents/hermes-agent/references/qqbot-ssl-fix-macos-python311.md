# QQBot SSL 证书问题修复（macOS Python 3.11）

## 问题现象

QQbot 在 macOS 上启动时 SSL 证书验证失败，错误如下：

```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] 
certificate verify failed: unable to get local issuer certificate
```

Gateway 日志显示：
```
aiohttp.client_exceptions.ClientConnectorCertificateError: 
Cannot connect to host api.sgroup.qq.com:443 ssl:True
```

## 根因

macOS 上通过 python.org installer 安装的 Python 3.11，其 OpenSSL 证书路径
`/Library/Frameworks/Python.framework/Versions/3.11/etc/openssl/cert.pem` 不存在。
Python 的 ssl 模块无法找到 CA 证书，导致所有 HTTPS 连接失败。

## 修复步骤

### 1. 确认 Python 3.11 的证书路径

```bash
python3.11 -c "import ssl; print(ssl.get_default_verify_paths())"
```

输出示例：
```
DefaultVerifyPaths(
    cafile=None, 
    capath=None, 
    openssl_cafile='/Library/Frameworks/Python.framework/Versions/3.11/etc/openssl/cert.pem',
    openssl_capath='/Library/Frameworks/Python.framework/Versions/3.11/etc/openssl/certs'
)
```

注意：`openssl_cafile` 为 `None`（文件不存在），而 `openssl_capath` 也可能不存在。

### 2. 确认 certifi 已安装

```bash
python3.11 -c "import certifi; print(certifi.where())"
```

正常输出：
```
/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/certifi/cacert.pem
```

### 3. 创建符号链接

```bash
mkdir -p /Library/Frameworks/Python.framework/Versions/3.11/etc/openssl
ln -sf /Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/certifi/cacert.pem \
  /Library/Frameworks/Python.framework/Versions/3.11/etc/openssl/cert.pem
```

### 4. 验证修复

```bash
python3.11 -c "import ssl; print(ssl.get_default_verify_paths().cafile)"
# 应输出: /Library/Frameworks/Python.framework/Versions/3.11/etc/openssl/cert.pem
```

### 5. 重启 Gateway

```bash
kill $(cat ~/.hermes/gateway.pid | python3.11 -c "import json,sys; print(json.load(sys.stdin)['pid'])")
cd ~/.hermes/hermes-agent && python3.11 hermes_cli/main.py gateway run --replace &
```

## 验证成功标志

Gateway 日志中应出现：
```
gateway.platforms.qqbot.adapter: [QQBot:1903435259] WebSocket connected to wss://api.sgroup.qq.com/websocket
gateway.platforms.qqbot.adapter: [QQBot:1903435259] Ready, session_id=...
```

## 何时需要此修复

- macOS 上运行 Hermes Gateway
- 使用 QQbot 或其他需要 HTTPS WebSocket 的平台
- 错误信息包含 `CERTIFICATE_VERIFY_FAILED` 或 `unable to get local issuer certificate`

## 相关错误模式

| 错误关键词 | 含义 |
|-----------|------|
| `CERTIFICATE_VERIFY_FAILED` | Python 无法验证服务器证书 |
| `unable to get local issuer certificate` | 根 CA 证书缺失 |
| `ssl.SSLCertVerificationError` | aiohttp/requests 的 SSL 验证失败 |

## 其他平台也可能受影响

此修复解决的是 Python 层面的 SSL 证书问题，以下平台适配器如果遇到同类错误也需要此修复：
- Discord（如果代理配置导致证书问题）
- 其他使用 aiohttp 的 WebSocket 连接
