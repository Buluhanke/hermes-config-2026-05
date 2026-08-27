---
name: 1688-sourcing
description: "1688找品选品 真Chrome登录态 computer_use 详情页抠规格阶梯价 找货源。Use when 用户要1688找货/比价/选品"
triggers:
  - 1688找品
  - 1688搜索
  - 找XX的1688货源
  - 去1688搜XX
---

# 1688 找品链（真 Chrome 版）

## 核心优势

- **登录态**：用户真实 Chrome（含 1688 已登录 cookie）
- **无签名**：所有操作在浏览器内完成，不走 HTTP API
- **无 IP 限制**：绕过 MTop 签名 + 中国 IP 要求
- **规格精准**：逐个点入 detail.1688.com 抠出真实规格+阶梯价

---

## 前置条件（首次需完成）

1. **油猴脚本**：Chrome 安装 Tampermonkey，装 `references/1688-script.md` 中的脚本
2. **cua-driver 授权**：`cua-driver browser-approve --profile existing`
3. **Chrome 已登录 1688**

---

## 标准操作流程

### 第一步：激活 Chrome + 导航到 1688

**方法A（cua_browser 精确绑定）**：
```python
# 获取 Chrome PID 和 window_id
computer_use(action="list_windows")

# 绑定
computer_use(action="cua_browser_state", pid=<pid>, window_id=<wid>)
computer_use(action="cua_browser_prepare", pid=<pid>, profile_mode="existing_profile")

# 导航
computer_use(action="cua_browser_navigate", url="https://s.1688.com/company/search.htm?keywords=关键词")
```

**方法B（computer_use 模拟操作，最可靠）**：
```python
computer_use(action="focus_app", app="Google Chrome")
computer_use(action="capture", app="Chrome", mode="som")
computer_use(action="click", app="Chrome", element=<搜索框元素>)  # 结果页搜索框 AXTextField，placeholder 是搜索词或"纸箱半高"
computer_use(action="type", app="Chrome", delivery_mode="foreground", text="搜索词")  # 多窗口 Chrome 必须 foreground
computer_use(action="key", app="Chrome", delivery_mode="foreground", keys="return")
```

> ⚠️ **搜索入口铁律（2026-08-19 实测，曾因此返工）**：**绝不**用 `set URL` 带 `?keywords=` 参数导航来搜 1688。
> 1688 会把 `s.1688.com/s/1688search?keywords=...` **重定向上清参数**成 `offer_search.html`（无关键词），
> 结果变成空搜 → 出鞋/工艺品/无纺布袋等乱品。中文编码（UTF-8 `%E7%BA%B8%E7%AE%B1` 或 GBK `%D6%BD%CF%E4`）都救不了，因为根因是重定向不是编码。
> **唯一可靠入口 = 点进页面内搜索框 + type 中文 + 回车**（走真实表单提交，URL 带 `spm=...searchbox.0` 才是真搜）。
> 验证：结果页 `document.title` 含搜索词、搜索框 `.value` 等于搜索词、才算成功。

### 第二步：油猴脚本翻页提取列表

脚本位置：`references/1688-script.md`

### 第三步：逐个进入详情页抠规格

**铁律：绝对不能只看列表页标题**，必须逐个点进详情页。

```python
computer_use(action="capture", app="Chrome", mode="som")
computer_use(action="click", app="Chrome", element=<商品链接元素>)
computer_use(action="list_windows")  # 找新 tab 的 window_id
computer_use(action="capture", app="Chrome", mode="ax")
```

详情页在 iframe 中时：直接导航到 `https://detail.1688.com/offer/{id}.html` 绕过。

### 第四步：提取详情页数据

用 `browser_console` 在详情页执行 JS：
```javascript
(function(){
    const title = document.querySelector('.title, h1')?.textContent?.trim() || '';
    const priceText = document.querySelector('.price')?.textContent?.trim() || '';
    const minOrder = document.querySelector('.min-order')?.textContent?.trim() || '';
    const address = document.querySelector('.address')?.textContent?.trim() || '';
    const shopName = document.querySelector('.shop-name')?.textContent?.trim() || '';
    const priceTable = document.querySelector('.price-quantity-table, table.price-table');
    let tieredPrices = [];
    if (priceTable) {
        tieredPrices = Array.from(priceTable.querySelectorAll('tr')).slice(1).map(row =>
            Array.from(row.querySelectorAll('td')).map(c => c.textContent.trim())
        );
    }
    return JSON.stringify({ title, priceText, minOrder, address, shopName, tieredPrices }, null, 2);
})()
```

---

## 输出格式

直接输出表格，不需要单独 MEDIA 文件：

```
| 序号 | 商品标题 | 规格 | 阶梯价 | 起批量 | 销量 | 供应商 | 发货地 | 详情链接 |
```

---

## 铁律

1. **供应商地域**：除非用户明说地域（如「江浙沪」），否则**不加 province 限制、全国搜**。2026-08-24 用户只说「找 46x26x10cm 纸箱」，助手擅自加江浙沪 province → 用户骂「什么乱七八糟的」。新任务默认 `--prov ''`（关地域），见 `1688-search-cn-gb-region-skill` 坑50。
2. **规格匹配**：只找尺寸完全匹配的（16×16×16cm），不是这个规格的不要推荐
3. **数据来源**：必须逐个点进详情页抠规格，绝不只看列表页标题
4. **用完关浏览器**：只关临时标签页，不动用户主窗口
5. **品类硬卡双条件**：详情页品类判定必须「品类词命中 AND 非排除品类」——裸品类词（如裸`牛皮纸`）会把"配牛皮纸包装"的电器/服装误收，必须加 `EXCLUDE_SIG`（电器/数码/五金/服装/玩具…）先排。详见下方「品类硬卡太宽」坑。
6. **非标尺寸无精确现货 → 近邻定制兜底**：精确命中 0 不等于没货，跑 `find_near.py` 找含目标某轴的近邻可定制厂（如 25×13×32 无现货但 26×13×33 差1cm同刀模），结论给「可定制+最近现货+推荐厂」。详见下方「近邻定制兜底」。

---

## ⚠️ 本 skill 已退休（2026-08-26 lineage 杂交裁定）
规则已证伪/被取代：computer_use 模拟点击 + 油猴脚本 + Playwright/9333 路径在 1688 上脆弱或崩溃（详见 `1688-search/1688-search-cn-gb-region-skill` 坑 13/15/26/33/41）。
**新任务一律走 `1688-sourcing-router` → `cdp1688.py`（后台隐藏 CDP Chrome + skuMapOriginal 监听，零风控零焦点抢）。**
本文件仅保留作历史 lineage 参考，勿再作为主路径使用。

## 常见问题

- **登录弹窗**：Chrome 的 1688 登录态已过期，需重新登录
- **无阶梯价**：需先点"立即订购"或"加入进货单"展开价格表
- **iframe 内元素找不到**：直接导航到详情 URL 绕过
- **搜索结果假数据**：真实 Chrome 不存在此问题，假数据只出现在代理IP被标记时

---

## Support Files

- `references/1688-script.md` — 油猴脚本完整源码（搜索页翻页提取 + 详情页 JS 提取）
- `references/chrome-ax-tree-extract.md` — 从 computer_use AX capture 元素文件解析商品数据的坐标定位法

---

## ⚠️ Chrome 双进程陷阱（2026-08-16 实测）

### 现象
用户已登录 1688 的 Chrome 启动时带 `--remote-debugging-port=9222`，`computer_use list_windows` 能看到窗口且 `capture` 返回 AX 树，但 CDP `Runtime.evaluate` JS 评估**无报错却返回空内容**（cross-process 沙盒限制）。

### 根因
同一 Chrome profile 不能被两个独立进程同时以同一 debugging port 绑定。Chrome PID A（用户原有进程）有登录态；Chrome PID B（新启动带调试端口的进程）共享 profile 文件但不继承调试端口，且 CDP JS 评估对 PID A 窗口返回空。

### 诊断
```bash
lsof -i :9222 | grep LISTEN
ps aux | grep "Chrome.*remote-debugging"
```

### 应对

**方案1（首选）：读 AX 树快照 JSON**
`computer_use capture` 成功时，元素数据同步写入 `~/.hermes/cache/computer_use/elements_<hash>.json`，从中解析商品数据（见 `references/chrome-ax-tree-extract.md`）。

**方案2：新标签页绕过主窗口**
用 `curl http://localhost:9222/json` 列出的非系统 page tab，CDP JS 评估对其正常。创建新标签页后 `Page.navigate` 导航。

**方案3：详情页直接摸 URL**
商品 ID 从 AX 树图片 URL 或链接 URL 提取，直接导航到 `detail.1688.com/offer/{id}.html`（无需登录即可看规格）。

### 禁止
- ❌ 用 `set URL` 带 `?keywords=` 参数搜 1688（重定向清空 → 空搜 → 乱品，见上方铁律）
- ❌ 用 `location=江浙沪`/`province=` 等 URL 参数做地域筛选（1688 同样重定向丢弃）
- ❌ 提取商品时全页扫 `detail.1688.com/offer/` 链接（主列表商品是 JS 跳转，无静态 `a href`；全页扫只能扫到浮窗/客服推荐 → 乱品）。只取主列表卡片自带的 `similar_search.html?offerIds=数字` 链接 ID。
- ❌ 仅读 `document.body.innerText` 判断主列表（1688 SPA 异步，innerText 常仅 ~1900 字符壳子；要以 `similar_search?offerIds=` 链接是否出现为准）

### 已证可用的真方法（推翻旧"双进程陷阱"结论）
- ✅ **AppleScript `execute active tab javascript` 对真实登录 Chrome 完全可用**（本机 2026-08-19 实测：
  读 DOM、dispatchEvent 点江浙沪、提取 offerId、读详情页规格 全部跑通）。
  旧 SKILL 说"osascript do JavaScript 对已登录 Chrome 超时/禁止"是**错误的**，已更正。
- ✅ **详情页直接导航 `detail.1688.com/offer/{id}.html`** 读规格（无需登录即可看 SKU 表）。
- ✅ 读 JS 文件必须用 `as «class utf8»`（否则中文变乱码，见 `references/1688-dom-driver.md`）。


## 品类硬卡太宽会混入「电器/蹭牛皮纸包装」无关品（2026-08-27 实战翻车 + 已修，同源 `1688-search-cn-gb-region-skill` 坑55）
搜 `25*13*32cm 牛皮纸手提袋` 时，候选池混进大量**电器/数码**（详情页写"配牛皮纸包装"），旧 `CARTON_SIG` 含裸 `牛皮纸` 单字 + `包装盒|纸盒`，这类页品类词命中 → 被误当手提袋核验甚至误命中。用户当场抓出「找到电器去来」。
- **根因**：品类正则把"页面提到牛皮纸"当"这是牛皮纸袋"，没排除借纸包装蹭词的非纸袋品类。
- **修法（已落地 `1688-search/1688-search-cn-gb-region-skill/scripts/cdp1688.py`）**：① `CARTON_SIG` 收紧——去掉裸 `牛皮纸` 单字与 `包装盒|纸盒`，锁定 `手提袋|纸袋|购物袋|包装袋|牛皮纸袋|牛皮纸手提袋|牛皮纸盒|纸箱|瓦楞|飞机盒|…`（纸箱任务仍由 纸箱|瓦楞|飞机盒 等词覆盖，不受影响）；② 新增 `EXCLUDE_SIG` = `电器|数码|数据线|充电器|适配器|电源|插座|灯具|LED|五金|工具|机械|电机|水泵|开关|插头|电池|耳机|音箱|手机|平板|电脑|键盘|鼠标|服装|鞋|袜|玩具|文具|家具`，在品类判定**之前**先查，命中即跳过；③ `page_title`/`title_text` 全部 `str()` 化防类型误判。
- **铁律**：任何「纸袋/手提袋」类任务，搜词宁可多词合并（坑40）也**绝不**靠裸品类词兜底；详情页品类判定必须「品类词命中 AND 非排除品类」双条件。改后 `python3 -m py_compile scripts/cdp1688.py` 验证。
- **识别信号**：结果里出现非目标品类（电器/服装/玩具）却标 HIT → 第一反应是品类正则太宽，加 `EXCLUDE_SIG` 而非怀疑尺寸匹配。

## 精确尺寸无现货 → 近邻定制兜底（2026-08-27 实战，复用 `find_near.py` / `find_near_251332.py`）
25×13×32 牛皮纸手提袋精确命中 0（全是帆布托特包），但近邻牛皮纸袋厂众多（如 `1066611511095` 有 26×13×33，差1cm同刀模；其余主流 32×11×25 / 40×13×31）。
- **正确收尾（不要报「没货」就停）**：跑 `scripts/find_near.py`（或针对本任务的 `scripts/find_near_251332.py`）—— 抓每个卖家 SKU 里**含目标某轴（25/13/32）的 near-size 清单**，输出「谁有相近尺寸 → 谁可定制切该尺寸」。结论应是「无精确现货、可定制 + 最近现货尺寸 + 推荐定制厂」，而非单纯「查无」。
- `find_near_251332.py` 已落盘（复刻 `find_near.py` 结构，DIM/NEAR/CAT 顶部常量可改），跑法：`python3 -u scripts/find_near_251332.py`，输出 `store/25x13x32_near.json`（`exact` / `near` 分桶）。

## 2026 更优方案参考（全网调研 2026-08）
第三方 1688-cli（superjack2050, MIT）复用真实 Chrome 登录态、输出结构化 JSON，可作补充；
但本机以 CDP 后台 Chrome + mtop skuMapOriginal 监听为主（零风控、零焦点抢），不替换。
官方 API 仍须企业资质；MTop 签名难度 4/5，本机无住宅代理不通；付费爬虫(ShopAPIS/HioBuy)需花钱。
开源逆向：QuoVadis86/ai-reverse（1688 MTOP SDK + MCP）。
