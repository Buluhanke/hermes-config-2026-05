# 外部 Web 服务调用失败模式 (2026-06-14)

## 背景
Web-Check 等外部服务无法通过 Hermes 直接调用。

## 失败模式

### 1. 浏览器导航 CSP/安全策略阻止
```
browser_navigate("https://web-check.xyz") → net::ERR_BLOCKED_BY_CLIENT
```
**原因**: 页面 CSP 头、adblock 扩展、或浏览器安全策略阻止加载。
**对策**: 不要依赖浏览器加载外部分析工具页面。

### 2. API 端点 403 Forbidden
```
curl -s "https://web-check.xyz/api/check?url=..." → 403 Forbidden
```
**原因**: 在线版 API 有访问限制，未授权 IP/请求头被拒。
**对策**: 不在 Hermes 上调用在线版 API。

### 3. Docker 自部署不可用
```
docker pull lissy93/web-check → command not found
```
**原因**: Mac mini 无 Docker，用户也禁止安装 Docker。
**对策**: 不要建议 Docker 部署方案给用户。

## 通用规则
- 外部 Web 分析工具 (Web-Check 等) → Hermes 无法自动调用
- 用户想用时 → 手动打开链接，不要提 Docker
- 需要批量分析时 → 写 Python 脚本直接调各 API (需 API key)，不调 Web-Check

## 参考
- 项目: [lissy93/web-check](https://github.com/lissy93/web-check)
- 在线版: https://web-check.xyz