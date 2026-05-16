---
name: baidu-ocr
description: 百度OCR图片文字识别 — 识别图片中的文字，支持通用文字识别、身份证、名片等
version: 1.0.0
author: Hermes Agent
requires_environment:
  - BAIDU_APP_ID
  - BAIDU_API_KEY
  - BAIDU_SECRET_KEY
---

# 百度OCR图片文字识别

调用百度AI开放平台OCR API识别图片中的文字。

## 配置

已在 `.env` 中配置：
- `BAIDU_APP_ID=7699346`
- `BAIDU_API_KEY=qBU5XnfWTHUuEVmfY13dC4Ka`
- `BAIDU_SECRET_KEY=Ygs0iNyC2H8YDDp7UleqvbyVlnD0DVnb`

## 用法

### 获取 Access Token
```bash
source ~/.hermes/.env
TOKEN=$(curl -s "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=$BAIDU_API_KEY&client_secret=$BAIDU_SECRET_KEY" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

### 通用文字识别（本地图片）
```bash
source ~/.hermes/.env
TOKEN=$(curl -s "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=$BAIDU_API_KEY&client_secret=$BAIDU_SECRET_KEY" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
BASE64=$(python3 -c "import base64; print(base64.b64encode(open('图片路径.png','rb').read()).decode())")
curl -s "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=$TOKEN" --data-urlencode "image=$BASE64" | python3 -m json.tool
```

### 通用文字识别（网络图片URL）
```bash
source ~/.hermes/.env
TOKEN=$(...)
curl -s "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=$TOKEN" -d "url=https://example.com/image.jpg"
```

### 准确版文字识别
```bash
curl -s "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate?access_token=$TOKEN" --data-urlencode "image=$BASE64"
```

## 可用接口（当前app已验证）
| 接口 | 端点 | 状态 |
|------|------|------|
| 通用文字识别 | `/rest/2.0/ocr/v1/general_basic` | ✅ 可用 |
| 准确文字识别 | `/rest/2.0/ocr/v1/accurate` | 需权限 |
| 通用物体识别 | `/rest/2.0/image-classify/v2/advanced_general` | ❌ 无权限 |
\n## 注意\n- 使用 `--data-urlencode` 传base64，不要用 `-d` 直接拼接（特殊字符会出错）\n- 免费额度：个人实名认证后每月1000次，企业2000次\n- 入口是 ai.baidu.com（不是 cloud.baidu.com）\n\n## 参考\n- `references/baidu-ocr-test-results.md` — 实际测试结果、踩坑记录、免费额度领取指引
