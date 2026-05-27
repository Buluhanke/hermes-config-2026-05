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
