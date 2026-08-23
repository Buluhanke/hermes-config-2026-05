# 1688 搜索方案对比实测 (2026-08-19)

基准任务: 17.5*17.5*8.5cm 纸箱, 江浙沪, 找 ≥5 个含该规格的商品链接
目的: 在现有 skill (方案0) 基础上, 全网找更优方案并逐个实测对比

## 方案0: 现有 skill (AppleScript 驱动真实 Chrome + 解析内联 HTML + 逐个开详情页) ✅
- 状态: 已验证可用 (17.5 任务跑通 5 个, 16*16*16 任务跑通 2+ 个)
- 优点: 复用真实登录态, 本地 IP, 不踩地理封锁, 零外部依赖
- 缺点: 需开 N 个详情页, 慢, 批量开触发 CAPTCHA
- 优化: check_batch_optimized.scpt (降速8s + 单批≤3 + 命中≥5即停)

## 方案1: 接口直连 h5api.m.1688.com (mtop.WirelessRecommend getOfferList) ❌ 已排除
- 接口: https://h5api.m.1688.com/h5/mtop.relationrecommend.WirelessRecommend.recommend/2.0/
  - appId=32517, method=getOfferList, params 含 keywords/beginPage/pageSize/province/charset=GBK
  - 签名: sign = md5(_m_h5_tk前半段 + "&" + t + "&" + appKey + "&" + data), appKey 固定 12574478
- 尝试A 裸 urllib: TLS 指纹被识 → `{"ret":["FAIL_SYS_USER_VALIDATE","RGV587_ERROR::SM::哎哟喂,被挤爆啦"]}` 验证码惩罚页
- 尝试B 真实 Chrome fetch: 从 s.1688.com 跨域 fetch h5api → CORS 拦截, 空返回
- 尝试C curl_cffi impersonate=chrome120 (本机已装 0.15.0) + 新鲜 _m_h5_tk → 仍 RGV587_ERROR
- 根因: 阿里对"非浏览器完整流程"的 h5api 调用直接丢验证码; 需中国住宅代理 + 真实浏览器行为指纹, 本环境无代理
- 结论: 纯接口直连在本环境三连击跑不通, 不纳入升级方案

## 方案2: 油猴脚本 (Tampermonkey, GM_xmlhttpRequest 跨域) ❌ 实测失败 (CSP 拦截)
- 脚本已成功安装并 enabled (Tampermonkey 存储确认: 1688_extract.user.js, matches=s.1688.com/selloffer/offer_search.htm*)
- 但 1688 搜索页 AX 树无浮层/按钮, hasGM=undefined, 剪贴板无 offerId → 脚本未注入
- 根因: 1688 返回严格 CSP 头, 阻止 Tampermonkey content script 注入 (GitHub 等站 CSP 宽松能跑, 1688 不行)
- 实测操作链 (全自动化, 无需用户): 本地 http.server 托管 .user.js → Chrome 打开脚本 URL → Tampermonkey 安装页 → 前景点击"安装" → 存储确认 enabled → 1688 页 AX 树验证无注入
- 结论: 方案2 在 1688 上被 CSP 拦截, 排除。不要再把油猴当 1688 的 JSON 捷径

## 方案3: 官方开放平台 API (alibaba.offer.search) ❌ 不适用
- 需企业认证 + AppKey/AppSecret + 签名; 个人用户基本拿不到
- 本场景 (偶尔搜几个纸箱) 不值得走这条

## 方案4: 1688-Scraper-MCP (第三方 DrissionPage 封装) ⏳ 待用户确认
- 能力: search_1688_products / get_product_detail_and_price / analyze_supplier_reliability
- 优势: 自然语言直接搜, Python 端过滤降 token, 持久化登录态自动过验证码
- 风险: 第三方仓库, 需装 Python 依赖 + 配置 mcp.json, 安全性需评估
- 决策: 等用户确认是否装第三方 MCP

## 汇总表
| 方案 | 可行性 | 速度 | 验证码 | 依赖 | 推荐度 |
|------|--------|------|--------|------|--------|
| 0 现有skill | ✅可用 | 中 | 批量触发 | 零 | ⭐⭐⭐ 当前主力 |
| 1 接口直连 | ❌不可行 | - | 必触发 | 需代理+伪装 | 弃用 |
| 2 油猴脚本 | ❌ CSP拦截 | - | - | 已装TMA | 排除 |
| 3 官方API | ❌门槛高 | - | - | 企业认证 | 不适用 |
| 4 第三方MCP | ⏳待确认 | 快 | 自动过 | 第三方依赖 | 需用户确认安全 |

## 关键发现 (写入 skill 坑)
- 搜索结果页的省份/店铺名是异步接口数据, HTML 只有骨架 (CSS class 如 `province .areas-list`), 无明文中文省份
- 但 `province=` URL 参数已锁江浙沪, 搜索结果页 offerId 全是江浙沪, 不必再筛
- 规格写法混用已覆盖: `17.5*17.5*8.5cm` / `17.5x17.5x8.5cm` / `17.5*17.5*8.5CM`; 飞机盒常拆写 `17.5*8.5(长*宽)`+`8.5cm(高)`
- _m_h5_tk cookie 存在于 1688 页面, token 格式 `58e1696480d67dedc3cd7f33b339f751_1787138316164` (下划线前为 token); TTL 短但本会话未过期
