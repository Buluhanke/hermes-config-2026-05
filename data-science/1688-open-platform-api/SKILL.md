---
name: 1688-open-platform-api
description: >-
  1688 Open Platform product data APIs — specification/SKU data, category
  attributes, and product details. Bypasses anti-scraping by using official
  REST APIs. Covers doc navigation, key endpoints, data structures, and auth
  requirements.
category: data-science
triggers:
  - 1688 product specification/SKU data
  - 1688 open platform API
  - e-commerce product data sourcing
  - supply chain product detail fetching
version: 1.0.0
---

# 1688 Open Platform API — Product & Specification Data

Official REST APIs for getting product/SKU/specification data from 1688, bypassing anti-scraping entirely.

> **⚠️ 使用限制：该 API 面向企业卖家/ISV 开发者，不是给纯买家用的。**
> 入驻需要：企业支付宝 + 营业执照 + 短信验证。纯买家账号（无1688店铺）无法通过 ISV 入驻注册。
> 对于纯采购/找品场景，优先用 CDP 浏览器自动化（`browser_navigate` + 已登录 Chrome），详见 `hermes-rpa` skill。
> 如果你确实需要企业级 API 接入，见下方入驻流程。

## Key APIs

### 1. Get Leaf Category Attributes (获取叶子类目属性)
**`alibaba.category.attribute.get`**
- URL: `POST https://gw.open.1688.com/openapi/param2/1/com.alibaba.product/alibaba.category.attribute.get/${APPKEY}`
- Input:
  - `categoryID` (Long, **required**) — 叶子类目ID
  - `webSite` (String, **required**) — `"1688"` 或 `"alibaba"`（国际站）
  - `scene` (String, optional) — `""` 空（默认）或 `"processing"`（加工定制品）
- Returns:
  - `attributes` (alibaba.category.AttributeInfo[]) — 类目属性信息
  - `attributeLevelMapStr` (java.util.Map, String) — 级联信息字符串，需强转成 map
  - `levelAttrRelList` (alibaba.category.PostLevelAttrRel[]) — **(已废弃)** 级联关系，仅1688返回
  - `errorMsg` (String) — 错误描述
  - `errorCode` (String) — 错误码
  - `success` (Boolean) — 是否成功
- Purpose: Get the attribute/specification template for a product category — which attributes exist, which are required, which are SKU-defining, what values are available.

**AttributeInfo fields:**
```json
{
  "attrID": 2489638,
  "name": "风格类型",
  "required": true,
  "fieldType": "enum",
  "isSKUAttribute": false,
  "attrValues": [{ "attrValueID": 91043051, "name": "气质通勤" }],
  "inputType": "1",
  "aspect": "0;",
  "isSpecPicAttr": false
}
```

**Key fields inside AttributeInfo:**
- `attrID` (Long) — 属性ID
- `name` (String) — 属性名（如"风格类型"、"颜色分类"）
- `required` (Boolean) — 是否必填
- `fieldType` (String) — 字段类型（enum, input, multiCheck 等）
- `isSKUAttribute` (Boolean) — **⭐ 核心**：true = 是SKU规格属性（决定SKU变体），false = 描述属性
- `attrValues[]` (array) — 可选值列表，每个 `{ attrValueID: Long, name: String }`
- `inputType` (String) — 输入类型（"1"=下拉选择, "2"=文本输入）
- `aspect` (String) — 粒度信息
- `isSpecPicAttr` (Boolean) — 是否规格图片属性

### 2. Get Product Details (获取商品)
**`alibaba.product.get`**
- URL: `POST https://gw.open.1688.com/openapi/param2/1/com.alibaba.product/alibaba.product.get/${APPKEY}`
- Input: `productID` (Long, required), `webSite`, `scene`
- Returns: `productInfo` (ProductInfo) with nested `attributes[]`, `skuInfos[]`, `saleInfo`, `shippingInfo`
- SKU fields: `cargoNumber`, `amountOnSale`, `price`, `retailPrice`, `skuId`, `specId`, `skuCode`, `priceRange[]`, `consignPrice`

### 3. Search SPU Info (查询标准化产品单元信息)
**`alibaba.category.searchSPUInfo`**
- URL: `POST https://gw.open.1688.com/openapi/param2/1/com.alibaba.product/alibaba.category.searchSPUInfo/${APPKEY}`
- Input: `categoryId`, `index`, `size` (max 20), `isNeedKeyAttr`, `isOnlyKeyAttr`

## API Doc Navigation

1. Open https://open.1688.com (no anti-scraping — official doc site)
2. **Quick navigation URLs** (skip the homepage menu):
   - Product APIs: `https://open.1688.com/api/apidocdetail.htm?aopApiCategory=product_new`
   - Category APIs: `https://open.1688.com/api/apidocdetail.htm?aopApiCategory=category_new`
   - Specific API doc (e.g. category.attribute.get): append `&id=com.alibaba.product%3Aalibaba.category.attribute.get-1`
3. **Extracting rendered content (JS-rendered pages)**: `page.content()` returns raw HTML with React root divs — parameter tables and API descriptions are client-rendered and won't appear. Use `page.evaluate()` instead:
   ```python
   page.evaluate("document.body.innerText")  # extracts rendered text content
   ```
   Or scroll to specific anchors:
   - `#api-2` — 请求 URL
   - `#api-3` — 系统级输入参数
   - `#api-4` — 应用级输入参数
   - `#api-5` — 返回结果
   - `#api-6` — 返回结果示例
4. Browse API category tabs: 会员, 商品, 类目, 订单, 支付, 物流
5. Sidebar menu lists all endpoints per category
6. "在线测试工具" button lets you test with real data after login — opens in a **NEW TAB**
7. Use dev console to find links: `document.querySelectorAll('a[href*="api"]')`

## Online Test Tool (在线测试工具)

The test tool opens in a **new browser tab** at:
```
https://open.1688.com/api/apiTool.htm?ns=<namespace>&n=<api_name>&v=<version>
```

The actual test form lives inside an **iframe** → `https://gw.open.1688.com/console/index.html?from=aop&lang=cn`

### Test Form Input Fields (inside iframe)

| Field | ID/Label | Description |
|-------|----------|-------------|
| AppKey | `appkey` | Your ISV application key |
| 签名密钥 | `signkey` | Your app secret |
| Access Token | (text input) | User authorization token |
| Refresh Token | (text input) | Token refresh token |
| 会员ID | (text input) | Member ID |
| 客户端超时 | — | Default: 5000ms |
| categoryID | Label: `* categoryIDLong` | Category ID (required) |
| webSite | Label: `* webSiteString` | `"1688"` or `"alibaba"` (required) |
| scene | Label: `sceneString` | Optional scene value |

### Test Form Buttons (inside iframe)

- **调用API** — Send the test request
- **签名工具** — Signature generation tool
- **提交问题** — Submit issue to support
- **获取 Token** — Get access token
- **刷新 Token** — Refresh token
- **重置** — Reset form

### How to use (Playwright)

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://open.1688.com/api/apiTool.htm?ns=com.alibaba.product&n=alibaba.category.attribute.get&v=1")
    page.wait_for_load_state("networkidle")
    
    # Find the iframe that contains the form
    frame = None
    for f in page.frames:
        if "gw.open.1688.com/console" in f.url:
            frame = f
            break
    
    if frame:
        # Fill in inputs
        frame.locator("#appkey").fill("your_app_key")
        frame.locator("#signkey").fill("your_sign_key")
        # Fill categoryID input (may need to locate by placeholder or structure)
        # Click "调用API"
        frame.locator("button").filter(has_text="调用API").click()
```

### Pitfalls
- **The form is in an iframe** — don't search for inputs in the main page, they won't be there
- **IFrame has no `screenshot()` method** — use `page.screenshot()` on the main page or capture the iframe by coordinates
- **`page.content()` returns empty React divs** — always use `page.evaluate("document.body.innerText")` to get rendered content
- **You must be logged into 1688** for the test tool to work — the tab may redirect to Taobao login if not authenticated
- **Hermes sandbox `input()` raises EOFError** — `input()` in the sandbox environment is not connected to a real TTY. Use `time.sleep()` loops or separate terminal commands instead of blocking on stdin

## ISV 入驻注册 (AppKey / AppSecret)

### 前置条件

注册前必须满足：
1. 1688 账号已绑定邮箱 — 否则点击"控制中心"弹"1688主站信息未填写"
2. 拥有**企业支付宝**（个人支付宝不行）
3. 拥有**营业执照**（原件照片，≤2MB，jpg/png/wbmp）
4. 手机号已绑定1688账号（用于收短信验证码）

> **纯买家账号（无店铺、无企业资质）无法完成 ISV 入驻。**
> 如果卡在企业支付宝/营业执照，说明用户不符合 ISV 开发者条件，应退回 CDP 浏览器自动化方案。

### ISV 身份类型

入驻页有6种身份可选，根据用户角色选择：

| 身份 | 适用场景 | 入驻门槛 | 推荐度 |
|------|---------|---------|--------|
| **软件开发商** | 开发电商工具，在服务市场售卖 | 中 | ⭐ |
| **采购服务商** | 自有采购系统对接1688（选品/下单/物流） | 高（企业资质） | ⭐ 买家首选 |
| **自研商家** | 商家自有系统对接1688店铺数据 | 最高（要求诚信通） | — |
| **代运营服务商** | 替商家做运营推广 | 中 | — |
| **店铺装修设计师** | 提供旺铺装修模板 | 低 | — |
| **综合服务商** | 工商财税、法律咨询 | 低 | — |

> 对于采购找品场景，选**采购服务商**最匹配。

### 入驻流程

1. **注册为 ISV 开发者** at https://open.1688.com
2. **登录**已有 1688/Taobao 账号
3. 点击 **控制中心** (顶部导航) → 自动跳转注册页 `open.1688.com/support/register`
4. 点击 **立即入驻** 选择身份（推荐：采购服务商）
5. 填写入驻表单：
   | 字段 | 说明 |
   |------|------|
   | 你的角色 | 自动填充，买家账号显示"下游平台角色/专业买家" 或"LP合作渠道商"（取决于账号类型） |
   | 登录账号 | 自动填充 |
   | 电子邮箱 | 从1688主站同步 |
   | 手机号 | 从1688主站同步 |
   | 短信验证码 | 点"获取验证码"→ 收短信 → 输入 |
   | 支付宝账号 | **必须绑定企业支付宝**（禁用，点按钮跳转绑定） |
   | 入驻原因 | 必填文字描述 |
   | 联系人钉钉 | 可选 |
   | 营业执照 | **必须上传**原件照片（≤2MB） |
   | 同意协议 | 必须勾选 |
6. 点击 **申请入驻**
7. 等待平台审核（通常1-3个工作日）
8. 审核通过后 → 控制中心 → 应用管理 → 创建应用 → 获取 AppKey/AppSecret

### 注册常见阻点

- **"1688主站信息未填写" dialog** — 邮箱未绑定。去 `member.1688.com/member/account_security` 绑定邮箱
- **邮箱绑定触发身份验证** — Taobao 要求人脸/手机验证码+证件/客服三种方式之一
- **企业支付宝不可用** — 个人支付宝无法绑定，这是最大的 blocker
- **营业执照不满足** — 需要原件照片，个体户执照也可
- **CDP 文件上传（隐藏 input[type=file]）** — 1688 上传按钮"plus 上传图片"是一个 `<button>`，点击后触发 JS 打开隐藏的 `<input type="file" style="display:none">`。需要在点击按钮后用以下方式定位并上传：
  1. 点击上传按钮（`browser_click(ref=...)`）
  2. 定位隐藏文件输入：`document.querySelector('input[type="file"]')`
  3. 通过 CDP `DOM.setFileInputFiles` 设置文件（需先获取 Node ID）
  4. 或者在 Playwright 中直接：在点击前用 `page.on('filechooser')` 监听文件选择器事件，然后在点击后自动设置文件路径
  **注意**：如果使用 aria-snapshot 找不到 hidden input，用 `browser_console` 执行 JS 查找。需用户提供文件绝对路径。

### 入驻审核通过后的 App 创建阻点（2026-05-10 新发现）

入驻审核通过后，"我的应用"页面要求**先订阅解决方案才能创建应用**。但 1688 解决方案列表页使用**虚拟滚动**（virtualized list）：

- 页面 DOM 中只有约 2 个 filter-chip 元素，没有实际的 solution card 元素
- `document.querySelectorAll('[class*=card]')` 返回 2（过滤标签），不是商品卡片
- 滚动页面也不会在 DOM 中创建卡片元素（虚拟滚动，React render window 外的不进入 DOM）
- `browser_click` 找不到任何卡片元素可点

**后果**：无法通过 CDP 浏览器自动化完成"订阅解决方案 → 创建应用"流程，必须用户手动操作一次。

**解决方案**：
1. **用户手动操作一次**（一次性，仅需这次）：在解决方案页面找到"买家对接"或"商品管理"分类下的方案，点击"订购" → 创建应用 → 拿到 AppKey/AppSecret → 告我配置
2. **直接用搜索替代**：用 `web_search_plus` (provider: searxng) 搜索 1688 商品，可返回商品名称、价格、成交数、店铺信息，绕过 API 需求

**推荐工作流**：
- 日常找品：优先用 `web_search_plus` (searxng) → 返回1688商品搜索结果（免费、即时）
- 需要商品详情（SKU/规格/价格区间）：用 CDP 操控已登录 Chrome 直接访问商品页
- API 方式（AppKey）：仅在用户手动完成一次解决方案订阅后启用

### CDP 浏览器是前提

登录流程涉及 Taobao/1688 认证。使用 CDP 模式（`browser.cdp_url` 指向持久化 Chrome）避免反复登录，详见 `hermes-rpa` skill。

## Login (浏览API文档)

1. Open https://open.1688.com in a browser
2. Click "请登录" at top-right → **redirects to Taobao login page** (1688 uses Taobao accounts)
3. Log in with 1688/Taobao credentials
4. After login, API doc pages (e.g. 在线测试工具) become functional

**Note**: The login page IS the Taobao login — don't look for a separate 1688 login form. If helping a user, have them open the browser locally; remote-controlled browsers (Playwright/Selenium) for this flow are fragile.

## Authentication (API Calls)

Requires OAuth2: register ISV → create app → APP_KEY + APP_SECRET → access_token.
All calls need: `access_token`, `_aop_signature` (HMAC-SHA256), `_aop_timestamp`.

## Pitfalls

- `alibaba.product.get` only queries products the authenticated user owns (seller-side)
- For public search, use `alibaba.product.search` or other search APIs
- Non-leaf categories may return empty attribute data
- `attributeLevelMapStr` is a JSON string, must be parsed
- `isSKUAttribute: false` = description attribute, not a SKU variant differentiator
- Spec `webSite=1688` — response structures differ from alibaba.com
- "在线测试工具" needs valid APP_KEY after login
- **纯买家无法入驻** — 企业支付宝 + 营业执照是硬性要求

---

## 身份认证流程 (Authentication)

1688 Open Platform 采用 **OAuth2.0 + RSA/SHA256签名** 双重验证。每次 API 请求必须在 HTTP header 或 URL 参数中携带：

### 认证三要素

| 参数 | 位置 | 说明 |
|------|------|------|
| `access_token` | Header `Authorization: Bearer {token}` 或 URL参数 | 用户授权令牌 |
| `_aop_signature` | URL 参数 | HMAC-SHA256 签名 |
| `_aop_timestamp` | URL 参数 | 请求时间戳（毫秒） |

### 签名计算公式

```
StringToSign = HTTP_METHOD + "\n"
            + gw.open.1688.com + "\n"
            + /openapi/param2/1/{namespace}/{api_name}/{appkey} + "\n"
            + access_token={token}&
            + categoryID={catID}&
            + webSite={site}
            + &_aop_timestamp={timestamp}

Signature = Base64(HMAC-SHA256(AppSecret, StringToSign))
```

> **注意**：参数必须按 **字母顺序** 排列后签名，漏参或顺序错乱会导致 `42` 签名错误。

### 获取 Access Token — 授权码模式

适用于有后端服务器的 ISV。

```
Step 1: 引导用户授权
GET https://oauth.1688.com/authorize?response_type=code&client_id={APPKEY}&redirect_uri={回调地址}&state=random

Step 2: 用户同意后回调带 code
redirect_uri?code=XXXXX&state=random

Step 3: 用 code 换 token
POST https://gw.open.1688.com/openapi/token/{APPKEY}
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=XXXXX&redirect_uri={回调地址}&client_id={APPKEY}&client_secret={APPSECRET}

Step 4: 响应
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 36000,
  "memberId": "..."
}
```

### 获取 Access Token — 在线测试工具（简化）

在开放平台的 **在线测试工具** 页面：
1. 填入 `appkey` + `signkey`（AppSecret）
2. 点击 **"获取 Token"** 按钮 → 自动弹出授权确认页
3. 用户在 iframe 内完成授权
4. Token 自动回填到表单

### Token 刷新

```
POST https://gw.open.1688.com/openapi/token/{APPKEY}
grant_type=refresh_token&refresh_token={refresh_token}&client_id={APPKEY}&client_secret={APPSECRET}
```

### 签名工具

开放平台提供在线签名工具（在线测试工具 iframe 内 "签名工具" 按钮），也可用 Python 本地计算：

```python
import hmac
import hashlib
import base64
import time

def sign_1688_request(app_key, app_secret, method, api_path, params):
    """
    method: GET 或 POST
    api_path: e.g. /openapi/param2/1/com.alibaba.product/alibaba.category.attribute.get/{appkey}
    params: dict of all parameters (including access_token, categoryID, webSite...)
    """
    timestamp = str(int(time.time() * 1000))
    
    # 按字母顺序排列参数
    sorted_keys = sorted(params.keys())
    param_str = "&".join(f"{k}={params[k]}" for k in sorted_keys)
    
    string_to_sign = (
        f"POST\n"
        f"gw.open.1688.com\n"
        f"{api_path}\n"
        f"{param_str}"
    )
    
    signature = base64.b64encode(
        hmac.new(
            app_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256
        ).digest()
    ).decode("utf-8")
    
    return signature, timestamp

# 使用示例
params = {
    "access_token": "YOUR_ACCESS_TOKEN",
    "categoryID": "1048182",
    "webSite": "1688",
}
api_path = f"/openapi/param2/1/com.alibaba.product/alibaba.category.attribute.get/{app_key}"
sig, ts = sign_1688_request(app_key, app_secret, "POST", api_path, params)
```

---

## 秘钥管理 (Key Management)

### AppKey / AppSecret 的生命周期

| 阶段 | 操作 | 风险 |
|------|------|------|
| 创建 | 控制中心 → 应用管理 → 创建应用 | — |
| 使用 | 嵌入代码 / 环境变量 | **禁止硬编码** |
| 轮换 | AppSecret 支持重新生成（最多保留2个） | 旧Secret失效需同步更新 |
| 废弃 | 删除应用或停用 | 及时清除代码中的凭证 |

### 安全最佳实践

```
✅ DO:
   - 将 AppKey/AppSecret 存入环境变量或密钥管理服务（AWS Secrets Manager / 阿里云 KMS）
   - 为不同环境（开发/测试/生产）创建独立应用
   - 定期轮换 AppSecret（建议每90天）
   - 使用最小权限：仅申请业务必需的 API 权限范围

❌ DON'T:
   - 硬编码在源代码（Git 历史永久保留）
   - 提交到 GitHub / GitLab
   - 在客户端（浏览器 JS）直接暴露 AppSecret
   - 在日志中打印签名结果或完整请求 URL（含 token）
```

### 多应用隔离策略

```bash
# 环境变量示例
export ALIBABA_APP_KEY_DEV="mock_app_key_for_dev"
export ALIBABA_APP_SECRET_DEV="mock_app_secret_for_dev"
export ALIBABA_APP_KEY_PROD="real_app_key"
export ALIBABA_APP_SECRET_PROD="real_app_secret"

# 代码中读取
import os
APP_KEY = os.environ["ALIBABA_APP_KEY_PROD"]
APP_SECRET = os.environ["ALIBABA_APP_SECRET_PROD"]
```

### AppSecret 重新生成流程

1. 控制中心 → 应用管理 → 选择应用
2. 基本信息 → **重新生成密钥**
3. 系统生成新 Secret（**旧 Secret 仍有24小时缓冲期**）
4. 更新所有使用旧 Secret 的系统
5. 确认新 Secret 正常工作后，旧 Secret 自动失效

> ⚠️ 重新生成后**无法找回**旧 Secret，请确保一次性完成所有系统迁移。

---

## 沙箱测试 (Sandbox)

### 1688 沙箱环境

1688 Open Platform **没有独立的公开沙箱域名**。沙箱测试有以下几种方式：

#### 方式1：在线测试工具（推荐）

在 API 文档页面点击 **"在线测试工具"**，打开带完整表单的 iframe：
- 无需写代码，直接填参数、点调用
- 使用 **真实 AppKey** 但消耗实际配额
- 测试数据：建议用小众类目 ID（如 `1048182`）或明确的测试商品 ID

#### 方式2：构造 Mock 响应

```python
# 用 responses 库拦截 requests，模拟 1688 返回
import responses
import json

@responses.activate
def test_category_attribute():
    mock_response = {
        "success": True,
        "attributes": [
            {
                "attrID": 2489638,
                "name": "风格类型",
                "required": True,
                "fieldType": "enum",
                "isSKUAttribute": False,
                "attrValues": [
                    {"attrValueID": 91043051, "name": "气质通勤"},
                    {"attrValueID": 91043052, "name": "简约休闲"}
                ],
                "inputType": "1",
                "aspect": "0;",
                "isSpecPicAttr": False
            }
        ],
        "attributeLevelMapStr": {}
    }
    
    responses.add(
        responses.POST,
        "https://gw.open.1688.com/openapi/param2/1/com.alibaba.product/alibaba.category.attribute.get/YOUR_APPKEY",
        json=mock_response,
        status=200
    )
    
    # 实际调用代码（会被 responses 拦截）
    result = call_1688_api(...)
    assert result["success"] is True
    assert result["attributes"][0]["name"] == "风格类型"
```

#### 方式3：测试店铺商品

- 用 `alibaba.product.get` 查询**自有店铺**的商品（API 只能查自己店铺）
- 或在开放平台申请**测试账号**（部分 ISV 方案提供）

### 测试数据建议

| 测试场景 | 建议参数 |
|---------|---------|
| 类目属性 | categoryID=`1048182`（女装），webSite=`1688` |
| 商品详情 | productID=`584051070147`（示例商品） |
| SKU 结构 | 找有多个 SKU 变体的商品测试 |
| 签名验证 | 用已知的 appKey/secret 先验证签名算法 |

---

## 真实API调用示例 (Working Examples)

### Python — 完整的签名 + 请求流程

```python
import requests
import hmac
import hashlib
import base64
import time
import json

APP_KEY = "your_app_key"
APP_SECRET = "your_app_secret"
ACCESS_TOKEN = "your_access_token"

def sign_request(app_key, app_secret, api_path, params):
    """计算 1688 HMAC-SHA256 签名"""
    timestamp = str(int(time.time() * 1000))
    sorted_keys = sorted(params.keys())
    param_str = "&".join(f"{k}={params[k]}" for k in sorted_keys)
    
    string_to_sign = (
        f"POST\n"
        f"gw.open.1688.com\n"
        f"{api_path}\n"
        f"{param_str}"
    )
    
    signature = base64.b64encode(
        hmac.new(
            app_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256
        ).digest()
    ).decode("utf-8")
    
    return signature, timestamp

def call_1688_api(api_name, namespace, params):
    """通用 1688 API 调用"""
    api_path = f"/openapi/param2/1/{namespace}/{api_name}/{APP_KEY}"
    
    # 合并系统级参数
    full_params = {
        "access_token": ACCESS_TOKEN,
        **params
    }
    
    signature, timestamp = sign_request(APP_KEY, APP_SECRET, api_path, full_params)
    full_params["_aop_signature"] = signature
    full_params["_aop_timestamp"] = timestamp
    
    url = f"https://gw.open.1688.com{api_path}"
    resp = requests.post(url, data=full_params)
    
    return resp.json()

# 示例1: 获取类目属性
result = call_1688_api(
    "alibaba.category.attribute.get",
    "com.alibaba.product",
    {"categoryID": "1048182", "webSite": "1688"}
)
print(json.dumps(result, ensure_ascii=False, indent=2))

# 示例2: 获取商品详情
result = call_1688_api(
    "alibaba.product.get",
    "com.alibaba.product",
    {"productID": "584051070147", "webSite": "1688"}
)
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### cURL — 快速调试

```bash
#!/bin/bash
# 1688 API 调用示例 (bash)
APP_KEY="your_app_key"
APP_SECRET="your_app_secret"
ACCESS_TOKEN="your_access_token"
TIMESTAMP=$(date +%s%3N)

# 构造参数（按字母顺序）
PARAMS="access_token=${ACCESS_TOKEN}&categoryID=1048182&webSite=1688"

# 计算签名 (macOS 上使用 gnu-sed 的 -E 支持)
STRING_TO_SIGN="POST
gw.open.1688.com
/openapi/param2/1/com.alibaba.product/alibaba.category.attribute.get/${APP_KEY}
${PARAMS}"

SIGNATURE=$(echo -n "$STRING_TO_SIGN" | openssl dgst -sha256 -hmac "$APP_SECRET" -binary | base64)

# 发送请求
curl -X POST "https://gw.open.1688.com/openapi/param2/1/com.alibaba.product/alibaba.category.attribute.get/${APP_KEY}" \
  -d "${PARAMS}&_aop_signature=${SIGNATURE}&_aop_timestamp=${TIMESTAMP}" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

### 响应解析示例

```python
# 解析类目属性 → 找出所有 SKU 规格属性
def parse_sku_attributes(api_response):
    if not api_response.get("success"):
        return {"error": api_response.get("errorMsg"), "code": api_response.get("errorCode")}
    
    sku_attrs = []
    for attr in api_response.get("attributes", []):
        if attr.get("isSKUAttribute") is True:
            sku_attrs.append({
                "id": attr["attrID"],
                "name": attr["name"],
                "values": [v["name"] for v in attr.get("attrValues", [])],
                "required": attr.get("required", False),
                "inputType": attr.get("inputType"),  # "1"=下拉, "2"=文本
            })
    
    return {"sku_attributes": sku_attrs}

# 使用
result = call_1688_api("alibaba.category.attribute.get", "com.alibaba.product",
                       {"categoryID": "1048182", "webSite": "1688"})
parsed = parse_sku_attributes(result)
for attr in parsed["sku_attributes"]:
    print(f"SKU属性: {attr['name']} | 可选值: {attr['values']}")
```

---

## 错误码排查 (Error Code Reference)

### 系统级错误码（所有API通用）

| 错误码 | 含义 | 原因 | 解决方案 |
|--------|------|------|---------|
| `12` | 无权限访问 | access_token 未授权该 API | 检查应用是否订阅了对应解决方案 |
| `28` | 签名不匹配 | 签名计算错误 | 确认参数顺序、编码、AppSecret 是否正确 |
| `42` | 签名校验失败 | 参数缺失或格式错误 | 确认所有必填参数都参与了签名计算 |
| `88` | token 过期 | access_token 失效 | 用 refresh_token 刷新，或重新授权 |
| `100` | 参数错误 | 传入参数值不合法 | 检查 categoryID 是否为 Long 类型、webSite 是否为 `1688` |
| `200` | 系统错误 | 1688 服务端异常 | 稍后重试，间隔 1-3 秒 |

### 应用级错误码（alibaba.category.attribute.get）

| 错误码 | 含义 | 解决方案 |
|--------|------|---------|
| `500_2` | 数据准备中，请稍后重试 | 数据正在后台加载，间隔 1-3 秒后重试 |
| `500_3` | 类目不存在 | 确认 categoryID 是叶子类目 ID，非父级类目 |
| `500_4` | 属性模板不存在 | 该类目可能没有发布过商品，属性模板未生成 |

### 商品级错误码（alibaba.product.get）

| 错误码 | 含义 | 解决方案 |
|--------|------|---------|
| `101` | 商品不存在 | productID 有误或商品已下架 |
| `102` | 商品不属于该用户 | `alibaba.product.get` 仅能查询自己店铺商品 |
| `103` | 商品未发布 | 商品状态不是 published |

### 排查流程

```
❓ 拿到错误响应
  ↓
是 success=false 还是 HTTP 状态码非 200？
  ├─ HTTP 4xx/5xx → 网络层问题 → 检查 VPN/代理/请求超时
  ├─ success=false + errorCode → 查上表
  └─ 签名错误 (28/42) → 优先检查签名计算逻辑
  ↓
确认 access_token 是否有效
  ├─ 在 https://open.1688.com 控制台验证 token
  └─ 尝试刷新 token
  ↓
确认 API 参数是否完整
  ├─ 必填参数：categoryID, webSite, access_token, _aop_signature, _aop_timestamp
  └─ 可选但影响结果：scene（加工定制品场景）
  ↓
用在线测试工具复现
  └─ 在 iframe 内填入相同参数，点"调用API"对比结果
```

### 签名错误（28/42）的 Debug 技巧

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 打印签名计算中间值
def sign_request_debug(app_key, app_secret, api_path, params):
    timestamp = str(int(time.time() * 1000))
    sorted_keys = sorted(params.keys())
    param_str = "&".join(f"{k}={params[k]}" for k in sorted_keys)
    
    string_to_sign = f"POST\ngw.open.1688.com\n{api_path}\n{param_str}"
    
    print("=== 签名调试 ===")
    print(f"StringToSign (原始):\n{string_to_sign}")
    print(f"AppSecret: {app_secret}")
    print(f"参数排序后: {param_str}")
    
    signature = base64.b64encode(
        hmac.new(
            app_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256
        ).digest()
    ).decode("utf-8")
    print(f"计算签名: {signature}")
    return signature, timestamp

# 用在线测试工具的"签名工具"按钮校验中间值
```

### Token 失效的判断

```python
def is_token_expired(response):
    """判断 token 是否过期"""
    if isinstance(response, dict):
        # 1688 错误响应格式
        if response.get("errorCode") == "88":
            return True
        if not response.get("success") and "token" in str(response.get("errorMsg", "")).lower():
            return True
    return False

# 自动刷新 token
def safe_call_with_refresh(api_func, *args, **kwargs):
    result = api_func(*args, **kwargs)
    if is_token_expired(result):
        print("Token 过期，刷新中...")
        new_token = refresh_access_token(REFRESH_TOKEN)
        set_access_token(new_token)  # 更新全局 token
        result = api_func(*args, **kwargs)
    return result
```
