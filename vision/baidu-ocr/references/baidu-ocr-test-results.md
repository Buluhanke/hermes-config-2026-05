# 百度OCR配置验证 & 踩坑记录

## 验证时间
2026-05-05

## 凭证
- AppID: 7699346
- API Key: qBU5XnfWTHUuEVmfY13dC4Ka
- Secret Key: Ygs0iNyC2H8YDDp7UleqvbyVlnD0DVnb

## 验证结果

| 接口 | 端点 | 结果 |
|------|------|------|
| 通用文字识别 | `general_basic` | ✅ 成功（读出了百度logo文字"百度"和截图文字） |
| 准确文字识别 | `accurate_basic` | ❌ No permission |
| 通用物体识别 | `advanced_general` | ❌ No permission |
| 菜品识别 | `dish` | ❌ No permission |

## 踩坑记录

### 1. base64 传参必须用 `--data-urlencode`
❌ 错误方式：
```bash
curl -d "image=$BASE64"  # 特殊字符(+ / =)会被破坏
```
✅ 正确方式：
```bash
curl --data-urlencode "image=$BASE64"
```

### 2. 图片格式问题
- PNG 直接 base64 传给 OCR 可能报 `image format error` (error_code: 216201)
- 用 Python 的 `base64.b64encode(open(file,'rb').read()).decode()` 生成 base64 可以正常工作
- macOS `base64 -i file | tr -d '\n'` 生成的 base64 有时会报格式错误

推荐方式（已验证）：
```bash
BASE64=$(python3 -c "import base64; print(base64.b64encode(open('图片路径.png','rb').read()).decode())")
```

### 3. Token 获取
```bash
source ~/.hermes/.env
TOKEN=$(curl -s "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=$BAIDU_API_KEY&client_secret=$BAIDU_SECRET_KEY" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```
Token 有效期约 30 天，建议每次调用前重新获取。

## 免费额度
- 入口：ai.baidu.com（不是 cloud.baidu.com）
- 个人实名认证：每月 1000 次
- 企业认证：每月 2000 次
- 每月自动刷新，不是一次性额度
