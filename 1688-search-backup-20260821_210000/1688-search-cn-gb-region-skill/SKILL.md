---
name: 1688-search-cn-gb-region-skill
description: 1688 站内搜索正确姿势（GBK关键词编码 + province URL筛选 + 解析内联HTML提取主列表offerId + 真实登录Chrome跑JS核对规格）。解决搜词乱码、筛选失效、提取到浮窗乱品、主列表不渲染、规格拆写、精确尺寸在翻页后六大坑。
category: ecommerce
---

# 1688 站内搜索（江浙沪/规格核对）正确姿势

## 触发场景
用户要在 1688 搜某商品（尤其带尺寸规格如 `16*16*16cm纸箱`、`17.5*17.5*8.5cm纸箱`），要求：
- 搜索范围锁定江浙沪（或某省份）
- 逐点开商品详情页核对规格，收集 ≥N 个含目标规格的商品链接
- 用户强调"必须读懂网页才能精确点击"，不要瞎猜坐标

## 八大坑（踩过的真实错误，按频次排序）
1. **无视用户已给的 URL（最高频）**：用户若已发过正确搜索 URL（尤其带 `province=` 的 `offer_search.htm?...`），**直接照用，别自作主张换端点/参数**。本会话曾因改用 `s.1688.com/s/1688search?location=...` 被重定向清空，绕了几十轮才回到用户一开始给的答案。用户给的链接/URL 优先于自己推导。
2. **关键词乱码**：1688 搜索关键词走 **GBK 编码**，不是 UTF-8。UTF-8 塞 URL 会被 1688 按 GBK 解成乱码（如"纸箱"→`绾哥`），搜出鞋/工艺品等无关品。
3. **URL 端点错**：`s.1688.com/s/1688search?keywords=...&location=...` 会被 1688 **重定向清空参数**（keywords/location 全丢）→ 变空搜索。正确端点是 `s.1688.com/selloffer/offer_search.htm`。
4. **筛选参数**：江浙沪筛选用 **`province` 参数**（不是 `location`），且只在 `offer_search.htm` 端点生效。值用 URL 编码：江苏=%E6%B1%9F%E8%8B%8F，浙江=%E6%B5%99%E6%B1%9F，上海=%E4%B8%8A%E6%B5%B7。逗号分隔。
5. **提取抓错区域**：1688 搜索主列表是 SPA，**商品 ID 不在 `<a href>` 里**（纯 JS 跳转），只在页面内联 HTML/JSON。扫 `a.href` 只抓到"找相似/旺旺/推荐浮窗"的乱品。必须解析 `document.documentElement.outerHTML` 抓 `detail.1688.com/offer/(\d+)` 和 `offerId=(\d+)`。
6. **主列表"不渲染"假象**：AppleScript `set URL` + `execute javascript` 驱动时，1688 主列表容器 `.search-offer-wrapper` 可能 `children=1` 空的（异步未注入）。但商品 ID 仍内联在 `outerHTML` 里——**不要依赖容器渲染，直接解析 outerHTML**（见坑 5）。
7. **精确尺寸常在第 2 页之后**：`beginPage=1` 常是"相似尺寸/同店"堆的，目标精确尺寸（如 `17.5*17.5*8.5cm`）可能一页 0 命中，翻 `beginPage=2`/`3` 才出现（实测 14 个第1页 0 命中，第2页 13 个里命中 5 个）。别因第 1 页 0 命中就下"没货"结论。
8. **规格拆写（飞机盒）**：部分商品（尤其飞机盒）不连写 `17.5*17.5*8.5`，而是 `17.5*8.5(长*宽)` + 另标 `8.5cm（高）`。纯连写正则匹配不到。目标是"正方形底面+高"时，需同时匹配 `17.5*17.5` 与高的 `8.5`（见 `scripts/check_spec.js` 的 joined||sq 双匹配）。
9. **验证码风控**：批量快速开详情页会触发 1688 **CAPTCHA Verification**（返回验证页，读不到规格）。降速（每个间隔 8-10s + 随机）+ 真人手动过一次验证可缓解。无法自动过验证码。
12. **接口直连 h5api 不可行（本环境已排除，勿再试）**：有人会想直接调 `https://h5api.m.1688.com/h5/mtop.relationrecommend.WirelessRecommend.recommend/2.0/`（appId=32517, method=getOfferList）拿 JSON 省去开详情页。实测 3 次全失败：①裸 urllib → TLS 指纹被识返回 `{"ret":["FAIL_SYS_USER_VALIDATE","RGV587_ERROR::SM::哎哟喂,被挤爆啦"]}` 验证码惩罚页；②真实 Chrome `fetch` → CORS 跨域拦截空返回；③curl_cffi `impersonate=chrome120`（本机已装 0.15.0）+ 新鲜 `_m_h5_tk` → 仍 RGV587_ERROR。根因：阿里对"非浏览器完整流程"的 h5api 调用直接丢验证码，需中国住宅代理+真实浏览器行为指纹。本环境无代理，**纯接口直连走不通**。
13. **油猴脚本在 1688 也被 CSP 拦截（已排除，勿再试）**：Tampermonkey 的 GM_xmlhttpRequest 跨域拿 JSON 看似能绕 CORS，但 1688 返回严格 **CSP 头**，直接阻止 Tampermonkey content script 注入——脚本装了且 enabled（`Tampermonkey 存储确认 1688_extract.user.js, matches=s.1688.com/selloffer/offer_search.htm*`），但 1688 搜索页 AX 树里无浮层/按钮、`hasGM=undefined`、剪贴板无 offerId，证明没注入。GitHub 等站 CSP 宽松能跑，1688 不行。**结论：油猴也不是 1688 的 JSON 捷径，排除**。验证操作链全程可自动化（本地 http.server 托管 .user.js → Chrome 打开 → Tampermonkey 安装页前景点击安装 → 存储确认 → AX 树验证无注入），无需用户手动。详见 `references/approach_comparison_20260819.md`。
14. **第三方 1688-Scraper-MCP 是可行升级（已集成，但需登录授权）**：仓库 `xiayumu034-crypto/1688-Scraper-MCP`（DrissionPage 驱动真实 Chromium，search_1688_products / get_product_detail_and_price / update_auth_cookie 等工具）。代码审查安全（无外传、登录态存本地 `drission_user_data`）。已接进 Hermes `mcp_servers.alibaba_1688_scraper`。**两个必踩的安装坑（已解决，勿重蹈）**：
    - **Hermes 网关给 MCP 子进程注入了 `PYTHONPATH=.../hermes-agent/venv/...`**，会污染外部 venv 的 pydantic 导致 `ModuleNotFoundError: pydantic_core._pydantic_core`。修法：建**隔离 venv**（如 `~/.hermes/1688-mcp/venv`，用 `/usr/local/bin/python3 -m venv`），再写一个 `bootstrap.py` 在 server.py 加载前 `os.environ.pop('PYTHONPATH')` + 强制 venv 的 site-packages 置顶 + 移除 hermes-agent venv 路径，command 指向 `bootstrap.py`。
    - **`/tmp` 会被系统清理**：早期把 venv 放 `/tmp/1688mcp`，用户离开期间被清，venv 丢失、MCP 启动报 `No such file or directory`。**一律放持久位置**（如 `~/.hermes/1688-mcp/`），不要放 `/tmp`。
    - **当前状态**：MCP 握手已验证成功（`serverInfo: 1688_Scraper_MCP`，`tools/call` 可调用），但 DrissionPage 的独立 Chromium 无登录态 → 调 search 返回 `ERROR_AUTH_REQUIRED`。需用户回来后调 `update_auth_cookie` 唤起真实 Chromium 扫码登录一次（登录态持久化）。登录后即能自然语言搜 1688 并拿结构化 JSON，比方案0省去开详情页。详见 `references/1688_mcp_setup.md`。
15. **Chrome 重启后 AppleScript JS 失效**：若发现 `execute javascript` 报"通过 Apple 事件中的 JavaScript 的功能已关闭"，是 Chrome 的 `AppleScriptJavaScriptEnabled` 被关（更新/设置重置）。修法：`defaults write com.google.Chrome AppleScriptJavaScriptEnabled -bool true` 后**重启 Chrome** 生效。不要以为是脚本问题。

16. **内联 JS 在 AppleScript 里正则必失效（本次实测）**：把含 `\\d`/`\\s` 的正则 JS 直接内联进 AppleScript 字符串，转义会被吞（`\\d`→空或单斜杠），执行返回 `[]` 或错配。修复：JS 一律写成独立 `.js` 文件，AppleScript 用 `read (POSIX file "/path") as «class utf8»` 读入再 `execute javascript`。本次 `scroll_sync` 第一版内联即返回空，改文件读（`extract_ids.js`）后正常。所有提取/核对脚本（`extract_ids.js`、`check_spec.js`）已是文件读，照用勿内联。

17. **只验规格不验品类会混入礼盒/包装盒（20*20*10cm 任务实测翻车）**：`check_spec.js` 只判"正文出现 20*20*10cm"就 `hit:true`，但 1688 把礼品盒/食品盒/烫金开窗盒也排进"纸箱"搜索结果池。实测 16 个 specHit 里 9 个是礼盒（如 `1069041013617`=跨境烫金开窗巧克力盒）。修复：规格命中**且**品类词（纸箱/瓦楞/快递箱/邮政箱/飞机盒/牛皮纸盒/搬家箱/收纳箱）出现在标题或正文前 2000 字**且非**礼盒信号（礼盒/烫金/巧克力/糖果/食品/蛋糕/首饰/化妆品/伴手礼）才判真纸箱。已固化成 `verify_carton.js`（带 `window.TARGET`）。注意：部分真纸箱厂页面只写"包装盒"不写"纸箱"，会被 false negative 误杀，需肉眼兜底或收紧搜索关键词（如加"瓦楞纸箱"）。

18. **AppleScript `execute javascript` 返回中文必乱码（¥0/起订:个/title乱码根因）**：osascript 把 JS 返回值当 MacRoman/UTF-8 混处理，中文直接变乱码，连累价格/标题/起批量全废。修复：JS 端把中文用 `esc(s)=s.replace(/[^\x00-\x7F]/g, c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'))` 转成 `\uXXXX` ASCII 串回传，本机用 `json.loads(payload.encode('utf-8').decode('unicode_escape'))` 解码。已固化成 `price_clean2.js` + 解码脚本（见 `scripts/`）。布尔/数字字段不受此影响，但凡涉及中文一律走 ASCII 编码通道。另：JS 正则含 `/`（如 `元|/|起`）必须写成 `\/` 否则 SyntaxError。

19. **首屏只渲染少量列表，须滚动懒加载才抓全（20*20*10cm 任务实测）**：1688 搜索结果主列表 SPA 首屏只注入约 13 个 offer，剩余靠 `window.scrollTo` 滚动触发懒加载。首屏直接提取只拿到 13-19 个 ID；AppleScript 驱动 `window.scrollTo(0, document.body.scrollHeight)` 滚动 8 次（每次 delay 1s）后再解析 `outerHTML`，才能抓到 ~100 个。不滚动会漏抓 80% 列表，导致命中数严重不足。固定套路：翻页 1-5 × 每页滚动 8 次 × 提取。

19b. **AppleScript `open for access` 写文件报 `-39 文件结尾错误` 且会截断续跑结果（16*16*16cm 任务实测翻车 2 次）**：批量脚本用 `open for access POSIX file OUT with write permission` + `set eof of f to 0` + 循环 `write ... to f` + 末尾 `close access f`，在 3~5 个 ID 后随机抛 `execution error: 文件结尾错误。 (-39)`，且 `set eof to 0` 会把已验结果清空导致**无法断点续跑**。根因：macOS AppleScript 文本文件句柄在循环写大串/多次 write 后状态异常。修复（已固化进 `check_batch_optimized.scpt` 与实战 `check_16.scpt`）：**所有文件 IO 改走 `do shell script "printf '%s\\n' " & quoted form of r & " >> " & quoted form of OUT` 追加**，读取已验 ID 也用 `cat` + `sed` 解析，全程不碰 `open for access`。续跑时只 `grep -c '"isCarton":true'` 计数，到 `STOP_HIT` 即停。此写法 89 个 ID 连跑零报错。

20. **规格匹配误中广告文案（尺寸只出现在标题/正文，不在真实 SKU 列表）—— 最致命的假阳性（16*16*16cm 实战翻车）**：初版 `verify_carton.js` 用 `body.innerText` 正则匹配 `16*16*16cm` 判命中，结果 `751990874462`（义乌圣天新材料）标题/正文含该尺寸被误判为纸箱，但详情页 SKU 实际只有 `15*15*15 / 17.5*17.5*17.5` 等 21 个尺寸、**根本没有 16*16*16**。修复（已固化进 `verify_carton.js`）：规格命中**唯一权威来源 = 真实 SKU 列表**——抓 `detail` 页 `.module-od-sku-selection` 内联尺寸（正则抽尺寸建集合，正方形底面另加 L*W...H cm(高) 拆写兜底），目标尺寸归一化(去 .0) 后必须在该集合内才 `skuHit=true`。复验 5 个原命中：4 个真有 16*16*16 通过，1 个误中正确剔除。SKU 块两种形态：① inline（尺寸 ¥价 库存 连写带价）；② size-bar（尺寸是选择条按钮，价默认显示第一个尺寸，需点中目标尺寸才出价，见坑 21）。抽集合逻辑通用。

21. **价格提取只拿到锚点价、拿不到目标尺寸精确价（Step6 原最大短板，已修）**：原 `price_clean2.js` 靠 `.offer-price` 选择器只能抠到首屏锚点（`¥0.2起`）。修复 = 升级版 `price_clean3.js`（已收编为首选）：① inline 布局正则从 SKU 块抠 `尺寸 ¥价 库存数`；② size-bar 布局自动 `click()` 目标尺寸 chip 再读 `.item-price-stock`；③ 退路取首个 `.item-price-stock`（多为默认选中=目标尺寸）。实测 4 个真纸箱全部返回精确价+库存：¥0.1(库存13万) / ¥0.18(库存9700万) / ¥1.4(库存9.8万) / ¥0.18(库存27万)。`price_clean2.js` 降级为兼容保留，新任务一律用 `price_clean3.js`。


## 工作流铁律：浏览器/扩展相关操作你自己驱动，别甩给用户
用户原话"你都能控制浏览器，你来操作啊"。凡是要在真实 Chrome 里装扩展、点安装按钮、拖文件、过验证码等**本可自动化的浏览器操作，直接用 computer_use / AppleScript 驱动，不要写一段"用户操作指南"甩给用户**。本机已具备：computer_use 后台驱动（som 点击/前景点击）、AppleScript `execute javascript` 读 DOM/驱动 Chrome、本地 `http.server` 托管文件给 Chrome 打开。仅当涉及**账户安全**（输密码、付费、点"同意"条款）才停手问用户。

## 正确流程（照做，不要自作主张改端点）

### Step 1：构造搜索 URL（用户给过就直接用，否则按此构造）
```
https://s.1688.com/selloffer/offer_search.htm?keywords=<GBK编码关键词>&spm=a26352.13672862.searchbox.0&province=<GBK编码省份>&beginPage=1
```
- 关键词 GBK 编码示例：`16*16*16cm纸箱` → `16*16*16cm%D6%BD%CF%E4`（`纸箱`=D6BD CFE4）；`17.5*17.5*8.5cm纸箱` → `17.5*17.5*8.5cm%D6%BD%CF%E4`
- 江浙沪 province：`%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%B7`（江苏,浙江,上海）
- 其他常见：广东=%E5%B9%BF%E4%B8%9C，浙江=%E6%B5%99%E6%B1%9F
- 翻页：改 `beginPage=2`（实测精确尺寸常在第 2 页）
- 验证搜索是否生效：打开后读搜索框值应为原关键词（`boxVal:"17.5*17.5*8.5cm纸箱"`），title 含关键词

### Step 2：在真实登录 Chrome 打开（不开调试端口）
用 AppleScript `execute javascript` 驱动已登录的真实 Chrome（守"只用登录态Chrome"规矩）：
```applescript
tell application "Google Chrome"
  set URL of active tab of front window to "<Step1的URL>"
  delay 7
  -- 提取主列表 offerId（见 Step 3）
end tell
```
> 禁止 `s.1688.com/s/1688search` 端点、禁止 URL 里用 `location=`、禁止 UTF-8 编码关键词。

### Step 3：提取主列表 offerId（解析内联 HTML，不是扫 a.href）
见 `scripts/extract_offers.scpt` 或内联：
```javascript
(() => {
  const html = document.documentElement.outerHTML;
  const ids = new Set();
  [...html.matchAll(/detail\.1688\.com\/offer\/(\d+)/g)].forEach(m => ids.add(m[1]));
  [...html.matchAll(/offerId["']?\s*[:=]\s*["']?(\d+)/g)].forEach(m => ids.add(m[1]));
  return JSON.stringify([...ids].filter(id => id.length >= 9 && id.length <= 14));
})();
```
- AppleScript 读 JS 文件必须 `read (POSIX file "/path") as «class utf8»`（否则中文乱码，匹配失败）
- 一次可抓到几十个真主列表 ID（验证：包含用户给的已知 ID）

### Step 4：逐个开详情页核对规格
详情页 URL：`https://detail.1688.com/offer/<id>.html`
- 通用核对脚本 `scripts/check_spec.js` **已参数化**：尺寸从 AppleScript 传 `TARGET="L*W*H"`（缺省 `16*16*16`），自动生成连写+拆写正则，覆盖 `*`/`×`/`x`/`X` 混用 + `cm`/`CM` 大小写 + CAPTCHA 检测
- 调用示例见 `scripts/check_batch.scpt`（AppleScript 批量循环，delay 8 防验证码，TARGET 注入方式在文件头注释）
- 命中 `hit:true` 即含目标尺寸；返回 `captcha:true` = 被验证码拦，需降速/真人过验证
- **规格写法实测**：1688 同尺寸多种写法都算命中——`17.5*17.5*8.5cm` / `17.5x17.5x8.5cm` / `17.5*17.5*8.5CM`（脚本正则 `i`+`[*×xX]` 已覆盖）；飞机盒常拆写 `17.5*8.5(长*宽)`+`8.5cm（高）`（L==W 时 SQ 拆写匹配兜底）

### Step 5：批量循环（AppleScript，降速防验证码）
见 `scripts/check_batch.scpt`。要点：`delay 8`、每个 ID 写一行结果到文件、try/on error 容错。

## 验证清单（每步确认）
- [ ] URL 是 `offer_search.htm` 端点（非 `s/1688search`）；用户若给过 URL 直接复用
- [ ] 关键词是 GBK 编码（非 UTF-8 百分号）
- [ ] province 参数存在且为江浙沪编码
- [ ] 打开后搜索框值 = 原关键词（非乱码）
- [ ] 提取的是内联 HTML 的 offerId（非 a.href 浮窗）
- [ ] 第 1 页 0 命中时翻 beginPage=2/3 再判
- [ ] 详情页命中非 CAPTCHA 页

## 常见错误自查
| 现象 | 根因 | 修复 |
|---|---|---|
| 搜出鞋/工艺品/无纺布袋 | 关键词 UTF-8 乱码 | 改 GBK 编码 |
| 搜索框空/变空搜索 | 用了 `s/1688search` 端点被重定向 | 改 `offer_search.htm` |
| 提取到"找相似/旺旺"链接 | 扫 `a.href` 抓到浮窗 | 解析内联 HTML |
| 主列表 children=1 空的 | 视线被容器渲染骗了 | 用正确 URL + 等 7s + 解析 outerHTML（不依赖渲染） |
| 第1页 0 命中就说没货 | 精确尺寸在翻页后 | 翻 beginPage=2/3 |
| 规格明明有却 hit:false | 拆写/符号大小写混用 | 用 scripts/check_spec.js 双匹配 |
| 详情页返回 CAPTCHA | 批量太快触发风控 | 降速 8s + 真人过验证 |

## 支持文件
- `scripts/extract_offers.scpt` — 提取主列表 offerId 的 AppleScript（内联 JS）
- `scripts/check_spec.js` — 详情页规格核对 JS（混用符号/大小写 + 连写拆写双匹配 + CAPTCHA 检测）
- `scripts/check_batch.scpt` — 批量开详情页核对 AppleScript 模板
- `scripts/check_batch_optimized.scpt` — 优化版（降速8s+单批≤3+命中≥5即停，防验证码）
- `references/spec_formats.md` — 1688 规格写法实测样本（连写/拆写/大小写）
- `references/approach_comparison_20260819.md` — 全网找更优方案的实测对比（方案0/1/2/3/4 + 汇总表）；含接口直连 AND 油猴脚本均已排除的根因
- `references/1688_mcp_setup.md` — 1688-Scraper-MCP 接进 Hermes 的完整安装实录（venv 隔离 + bootstrap.py 清 PYTHONPATH + 持久位置 + 登录授权流程）
- `references/1688_extract.user.js` — 油猴脚本样例（已实测被 1688 CSP 拦截，保留作反面教材，勿再依赖）
- `scripts/extract_ids.js` — 从内联 HTML 提取 offerId（独立文件读入，避开内联正则转义失效，坑16）
- `scripts/price_clean3.js` — **首选**详情页精确价+库存提取（坑21：兼容 inline + size-bar 两种 SKU 布局，自动 click 目标尺寸 chip 读 `.item-price-stock`，退路取首个 price-stock）
- `scripts/price_clean2.js` — 兼容保留（坑18 ASCII 安全回传），仅拿锚点价，新任务一律用 price_clean3.js
- `scripts/verify_carton.js` — 规格命中以**真实 SKU 列表**为权威（坑20：尺寸必须出现在 `.module-od-sku-selection` 尺寸集合，否则广告文案误中）+ 品类词 + 非礼盒信号 二次过滤
- `scripts/verify_carton_matrix.js` — **矩阵式尺寸首选**（坑30：长宽轴 `8x8（长宽）` × 高轴 `9cm（高）` 组合识别；`matrixHit = lwSet含(L*W) 且 hSet含H`；已修全角左括号 `（` 漏判）。TARGET 注入同 verify_carton.js
- `scripts/scroll_sync_2020.scpt` / `reverify_carton_2020.scpt` / `price_clean2_2020.scpt` — 20*20*10cm 任务实战脚本（翻页+滚动+复核+抠价，可改 TARGET 复用）
- `references/price_extraction.md` — 价格/起批量提取坑位（含坑21 两种 SKU 布局 + 假阳性案例）、ASCII 编码修法、20*20*10cm 实测价表
- `references/research_1688_alternatives_20260820.md` — 全网找更优方案调研 condensation（官方开放平台 API / 第三方 MCP / MTop 逆向 / 代理 IP，结论：本机无企业账号+无中国住宅代理，维持方案0）


22. **用 write_file / heredoc 写含正则的 .js 注入脚本时反斜杠被双写（本轮 verify_carton.js 翻车根因）**：`write_file` 与 shell heredoc 会把正则里的 `\d` `\s` `\.` 写成磁盘上的 `\\d`（双反斜杠），`execute javascript` 执行时正则语义全错（尺寸抽不出 / `skuHit` 恒 False）。`node --check` 只验语法不验正则语义，会假装通过。规避：**正则里一律用 `[0-9]` 代替 `\d`、`[ ]` 代替 `\s`、`[.]` 代替 `\.`**，彻底不写反斜杠；`esc`/`escR` 里必不可少的 `\u`/`\$&` 接受双写（它们不在主抽取路径上）。写完后用 `python3` 读字节数真实反斜杠数确认 `[0-9]` 行零反斜杠。

23. **内嵌 `<script>` 的 productPackInfo / sku1 / pieceWeightScale 是 SKU 假阳性陷阱（16*16*16 实战 751990874462 因此复活）**：为兜底未渲染的 size-bar，曾把含 `targetNorm` 的 `<script>` 文本并入 `skuTxt`，结果那些 script 含跨商品广告文案尺寸（同店其他款 / 推荐位），污染尺寸集合使本无该尺寸的商品误中。结论：**SKU 尺寸权威只认 `.module-od-sku-selection` 的 DOM 文本**，绝不并内嵌 script。内嵌 script 仅可用于"看结构"，不可用于"判命中"。

24. **Chrome 136+ 的 CDP WebSocket 被 `403 Forbidden`（本地脚本连不上）**：136 起 Chrome 默认拒绝非白名单 origin 的 CDP 连接。用 `--remote-debugging-port=9222` 起 Chrome 后，本地 Python/Playwright 连 `ws://127.0.0.1:9222` 会吃 403。**修法：启动 Chrome 时加 `--remote-allow-origins=*`**（引号包住，zsh 下 `*` 会被 glob 展开，必须 `'--remote-allow-origins=*'`）。否则任何 CDP/Playwright connectOverCDP 都连不上。

25. **1688 主列表链接结构已变，旧 `detail.1688.com/offer/<id>` 几乎消失（2026-08-21 实测）**：搜页商品链接现在主要是 `detail.m.1688.com/page/index.html?offerId=<id>`（移动详情页），旧桌面路径极少。若提取只匹配 `detail.1688.com/offer/(\d+)`，会**漏抓约 40%** 列表（实测同一次搜索 68→109 个 offerId）。**`extract_ids.js` 已是组合提取**（旧路径 + `[?&]offerId=(\d+)` + 内联 `offerId["']?\s*[:=]\s*["']?(\d+)`），覆盖新旧结构，勿改回单一正则。

26. **Playwright 比裸 CDP/AppleScript 好维护，但 headless 直连搜页必触发验证码（2026-08-21 实测，重要）**：
    - 用 `storage-state.json` 注入登录态**本身有效**（详情页直开带会话、4 已知 ID 全过），但** headless 直连搜页会被 1688 返回「驗證碼攔截」风控页**——无头指纹更敏感。
    - **正确姿势**：`chromium.connectOverCDP('http://127.0.0.1:9222')` 驱动**真实登录态的 CDP Chrome**（真人非无头路径），风控不触发。
    - **且搜页前必须先开 `www.1688.com` 首页暖场建会话，同 tab 再跳搜索**（called 暖场）。cold-navigate 直接跳搜索 URL 仍会被端点级风控踢回登录/验证码页（与坑1/登录态章节结论一致）。
    - 已收编为 `scripts/drive_playwright.js`（零额外 npm 依赖——GBK 编码复用 python3，不装 iconv-lite；复用 verify_carton.js + price_clean3.js）。前置：Chrome 以 chrome-cdp-profile（Profile）+ `--remote-allow-origins=*` 启动，CDP 9222 在线。
    - 环境变量可覆盖：`DIM`/`CARTON`/`PROV`/`PAGES`/`STOP_HIT`/`KNOWN`/`OUT`/`CDP`。例：`DIM=17.5*17.5*8.5 CARTON=纸箱 PAGES=5 node scripts/drive_playwright.js`。

27. **homebrew 系统 python3 与 hermes venv 的 playwright 二者独立**：本机 `/usr/local/bin/python3`（或无 brew 时 `/usr/bin/python3`）无 playwright；node/playwright 走 npm 全局。drive_playwright.js 用 `node`（已装 playwright + chromium 缓存）跑，不受 python 环境干扰。CDP Chrome 用系统 `/Applications/Google Chrome.app` 即可。

28. **node 跑 drive_playwright.js 需能 resolve playwright 模块**：playwright 装在 `~/.hermes/1688-pw/node_modules`，脚本在 skill 的 `scripts/` 目录，直接 `node scripts/drive_playwright.js` 会 `Cannot find module 'playwright'`。**修法**：`cd scripts && NODE_PATH=/Users/aimac/.hermes/1688-pw/node_modules node ./drive_playwright.js`（NODE_PATH 指向含 playwright 的 node_modules）。勿把 node_modules 塞进 skill 目录（污染分发包）。

29. **精确立方体用 `x` 记号双查，别只搜 `*`（2026-08-21 实测，精度关键）**：1688 搜 `16*16*16` 的 `*` 是**模糊匹配**——凡含某维度 16cm 的都排进池（47*16*16、62*16*16、宽16cm 等），非真立方体。搜 `16x16x16`（字母 x）才是**精确立方体**。drive_playwright.js 已内建**双记号搜索**（同时跑 `DIM` 与 `DIM_X=DIM.replace('*','x')`，合并去重），命中精度质变。若只要精确立方体，把 `DIM` 直接设成 `16x16x16` 亦可。

30. **矩阵式尺寸（长宽×高）是第三类尺寸写法，原脚本漏检（2026-08-21 实战翻车根因）**：部分卖家（尤其「彩盒定制」类）把尺寸拆成**两个 SKU 轴**，不在正文连写 `8*8*9`，而是 `8x8（长宽）` 在长宽轴 + `9cm（高）` 在高轴，组合后才等于 8×8×9cm。原 `verify_carton.js` 只匹配连写 `L*W*H`，**整类漏掉** → 误判「没货」。
    - **修法**：`scripts/verify_carton_matrix.js`（已固化首选）。三路命中：① 连写 `L*W*H`（保留原逻辑，限 `.module-od-sku-selection` DOM）；② 长宽轴正则 `([0-9.]+)[xX×*]([0-9.]+)[（(]?长宽` 建 `lwSet`；③ 高轴正则 `([0-9.]+)[cmCM]?[（）()]*高` 建 `hSet`；④ 组合串 `8x8（长宽）;9cm（高）` 直配。**`matrixHit = lwSet含(L*W) 且 hSet含H`**。TARGET 注入同原脚本（`window.TARGET='8*8*9'`）。
    - **坑中坑（已修）**：高轴的括号是**全角左括号 `（`(U+FF08)**，原正则只放了 `）`(右括号) → `hSet` 恒空 → 漏判。正则须用 `[（）()]*` 双括号覆盖。修后 677701816838（盒骏）正确 `matrixHit=True`。
    - **调用铁律**：matrix 脚本是独立文件，AppleScript 用 `read (POSIX file ...verify_carton_matrix.js) as «class utf8»` 读入（勿内联正则，坑16）。TARGET 注入后再跑。

31. **矩阵式卖家不在尺寸词搜索结果池，必须补「彩盒定制」词（2026-08-21 实测）**：搜 `8*8*9cm纸盒` / `8*8*9cm包装盒` 只返回**连写尺寸**卖家（8*8*8、13*8*9 等），**矩阵式卖家整批不在池内**。他们是「彩盒定制」类目，只有搜 `彩盒定制`（GBK `%B2%CA%BA%D0%B6%A8%D6%C6`）才排出来（677701816838 即在其中）。
    - **正确搜法**：同 DIM 跑**两组词**合并去重 —— ① `DIMcm纸盒`(GBK 纸盒=%D6%BD%BA%D0) ② `彩盒定制`。两组 offerId 合并验。否则漏掉整类货源，下「没货」结论是错的。（drive_playwright.js 的 `KW` 环境变量可传多词，逗号分隔。）

32. **搜索结果文件喂详情页前必须提纯 ID（2026-08-21 翻车）**：`extract_ids.js` 的返回是 `{"ids":[...]}`（一行一个搜索页），若直接把整行当 ID 列表喂 verifier，会把搜索页 JSON 当"商品ID"构造 URL → 详情页错乱、CAPTCHA 后脚本早退。
    - **修法**：先用 python 从 `提取文件` 里 `json.loads` 取 `ids` 字段、过滤 `i.isdigit() and 9<=len(i)<=14`，写成**纯数字 ID 每行一个**的文件，再喂 verifier 的 `paragraphs of (read ...)` 循环。verifier 的 `IDFILE` 必须指向这个纯 ID 文件，不是原始提取文件。

## 已验证样例（实战跑通，可直接复用）

**任务：矩阵式彩盒（8×8×9cm / 9×9×10cm，江浙沪）—— 必须用 verify_carton_matrix.js + 补「彩盒定制」词（坑30/31，2026-08-21 实战）**
- 这类卖家尺寸写法：`8x8（长宽）` 轴 × `9cm（高）` 轴 = 8×8×9cm（**不连写**，原 verify_carton.js 漏检）。
- 搜索词**两组合并去重**：① `8*8*9cm纸盒`(GBK `8*8*9cm%D6%BD%BA%D0`) ② `彩盒定制`(GBK `%B2%CA%BA%D0%B6%A8%D6%C6`)；端点 `offer_search.htm` + `province=江浙沪`，翻页 1-3。
- 提取 offerId 后**先提纯**（坑32：python 取 `ids` 字段过滤纯数字 9-14 位，写每行一个），再喂 `verify_carton_matrix.js`（TARGET=`8*8*9`）。
- **8×8×9cm 江浙沪命中 3 家**（全部矩阵式）：
  1. `677701816838` 义乌市盒骏包装（浙江义乌）✓ `8x8（长宽）×9cm（高）` ¥0.05 库存79万 1起批
  2. `783582821059` 温州瀚拓包装（浙江温州）✓ ¥0.06 库存999万
  3. `786814474290` 温州瀚拓包装（浙江温州）✓ ¥0.06 库存999万
- **9×9×10cm 江浙沪命中 4 家**（同一批矩阵卖家，全尺寸组合现做）：
  1. `677701816838` 义乌市盒骏包装 ✓ `9x9（长宽）×10cm（高）`
  2. `782048534122` 温州瀚拓包装 ✓
  3. `783582821059` 温州瀚拓包装 ✓
  4. `786814474290` 温州瀚拓包装 ✓
- 教训：① 矩阵式卖家**只在「彩盒定制」池**，尺寸词搜不到（坑31）；② `9cm（高）` 是全角左括号 `（`（坑30 已修）；③ 搜结果 JSON 不能直接当 ID 喂详情页（坑32）。

**任务：17.5*17.5*8.5cm 纸箱，江浙沪，≥5 个**
- 搜索 URL：`https://s.1688.com/selloffer/offer_search.htm?keywords=17.5*17.5*8.5cm%D6%BD%CF%E4&spm=a26352.13672862.searchbox.0&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%B7&beginPage=2`
- 第 1 页 14 个 0 命中（多为飞机盒 `17.5*8.5` 非正方形）；翻 `beginPage=2` 命中 5 个：
  1. `634522031289` 慈溪（浙江）✓ `17.5*17.5*8.5cm`
  2. `751990874462` 慈溪（浙江）✓ `17.5*17.5*8.5cm`
  3. `765857194469` 杭州（浙江）✓ `17.5*17.5*8.5CM`
  4. `634987797003` 慈溪（浙江）✓ `17.5x17.5x8.5cm`
  5. `708938768516` 慈溪（浙江）✓ `17.5*17.5*8.5CM`
- 教训：首屏 0 命中先翻页，别下"没货"结论（坑 7）

**任务：16*16*16cm 纸箱，江浙沪**
搜索 URL：同构，`keywords=16*16*16cm%D6%BD%CF%E4`，翻 3 页得 89 个唯一 offerId（江浙沪 province 服务端筛选生效）
- 规格复核用 `verify_carton.js`（坑20：以真实 SKU 列表为权威），价格用 `price_clean3.js`（坑21：精确价+库存）
- **真·16*16*16cm 纸箱（6 个，全部江浙沪，含精确单价/库存，均经 Playwright 驱动逐详情页实时复核）：**
  - `634522031289` 义乌圣天新材料（浙江义乌）✓ 16*16*16cm ¥0.2 库存756万 1个起批
  - `694009956651` 义乌箱当红包装（浙江义乌）✓ 16*16*16cm ¥0.3 库存97万 1个起批
  - `564506516477` 义乌丰狂顺易包装（浙江义乌）✓ 16*16*16cm ¥0.1 库存88万 1个起批
  - `680682547475` 义乌箱当红包装（浙江义乌）✓ 16*16*16cm ¥0.1 库存13万 1个起批
  - `647608648390` 义乌重远新材料（浙江义乌）✓ 16*16*16cm ¥0.18 库存9700万 3个起批
  - `727704740601` 浦江联恒包装（浙江金华浦江）✓ 16*16*16cm ¥1.4 库存9.8万 2个起批
- **假阳性剔除**：`751990874462`（义乌圣天新材料）正文含 16*16*16 但 SKU 实际只有 15*15*15 / 17.5*17.5*17.5 等，无 16*16*16，坑20 正确排除。
- 搜索 URL：`https://s.1688.com/selloffer/offer_search.htm?keywords=20*20*10cm%D6%BD%CF%E4&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD`
- 翻页 1-5 + AppleScript 驱动 `window.scrollTo` 滚动懒加载后共 ~100 个 offerId；`check_spec.js` 粗筛命中 16 个 `20*20*10cm`（specHit=true）
- **但其中 9 个非纸箱**（礼盒/包装盒/烫金开窗盒，如 `1069041013617`=跨境烫金开窗巧克力盒），用 `verify_carton.js`（规格命中 + 品类词 + 非礼盒信号）复核后仅 **7 个真·纸箱**：
  `708938768516`、`998552191936`、`634522031289`、`680808727007`、`919811645987`、`988478744578`、`990683696200`（浙江义乌/嘉兴/温州 + 江苏徐州，province 服务端筛选生效）
- 阶梯价/起批量已用 `price_clean2.js` 抠出（见 `references/price_extraction.md`），完整清单存 `~/Desktop/20x20x10_纸箱_江浙沪_找品结果.md`
- 教训：①首屏只渲染少量，须滚动 8 次再提取，否则漏抓 80% 列表（坑19）；②只验规格不验品类会混入礼盒（坑17），必须 `verify_carton.js` 二次过滤

## 备注
- 视觉通道（vision_analyze）本机可能 404（venv 污染 PIL）；本 skill 全程依赖 DOM 文字通道，不依赖视觉
- 用户确认的已知正确商品可先列入清单，再补亲验
- 脚本路径：`scripts/extract_offers.scpt`、`scripts/check_spec.js`（参数化 TARGET）、`scripts/check_batch.scpt`、`scripts/check_batch_optimized.scpt`（降速8s+单批≤3+命中≥5即停）
- 改尺寸只动 `check_batch*.scpt` 顶部 `property TARGET`
- **多方案优化时**：先备份本 skill（`cp -R` 到 `backup-<时间戳>/`），再逐个试新方案，最后给对比表。不要一上来就把方案列表抛回给用户选（用户明确说过会"不知所措"）。完整对比记录见 `references/approach_comparison_20260819.md`，工作流见 `multi-approach-evaluation` skill。

## 登录态与端点风控（2026-08-20 实测，已定论——所有新会话照此执行）

### 最终能力边界
| 通道 | 端点 | 自动化浏览器可用？ | 登录态要求 |
|---|---|---|---|
| 方案0（真 Chrome + AppleScript） | `s.1688.com/selloffer/offer_search.htm` + `detail.1688.com` | ✅ 可用（真人路径，非无头） | 用户真实 Chrome 登录态 |
| MCP `get_product_detail_and_price` | `detail.1688.com/offer/<id>.html` | ✅ 可用（免中转登录墙） | MCP 独立 Chromium 登录态（drission_user_data） |
| MCP `search_1688_products` | `s.1688.com/selloffer/offer_search.htm` | ❌ **端点级风控**：强制踢回 `login.taobao.com` 中转页 | 即便首页已登录、先过首页 session 再跳，照样踢 |

### 关键结论（勿重复试错）
1. **登录态已成功持久化**：`drission_user_data/` 里的 MCP 独立 Chromium 已登录 1688（`www.1688.com` 首页 `has_user=True`、`detail.1688.com` 直开商品页无墙）。来源：`scripts/verify_login.py` 实测。
2. **搜索页不是 cookie 域问题，是端点风控**：同会话先开首页再跳 `s.1688.com/selloffer/`，仍被踢回 `login.taobao.com`。与是否登录无关。来源：`scripts/verify_endpoints.py` 实测。
3. **二维码只在未登录时弹**：扫码入口 `member.1688.com`（1688 主站，非 taobao 中转）。已登录则打开即跳首页、不弹码。来源：`scripts/login_1688.py`。
4. **MCP 当前是"半自治"**：搜+抓 ID 仍走方案0（真 Chrome）；拿到 ID 后可用 MCP `get_product_detail_and_price` 走 `detail` 端点拿结构化价格（已登录、免验证码、比方案0 逐个开详情页更稳）。
5. **要让 MCP 搜索也通**：需改 `server.py` 的 `search_1688_products` 搜索 URL 换成不被风控的端点（待探索，非当前默认）。当前**不要**指望 `search_1688_products` 返回数据。

### 登录/验证脚本（已收编进本 skill，路径已全部相对化，勿在裸 repo 另存副本）
- `scripts/login_1688.py` — 唤起 MCP 独立 Chromium 走 `member.1688.com`，留 180s 窗口扫码；登录态写入 skill 内 `venv/drission_user_data`（与 `mcp/server.py` 共享）。
  - 用法：`<skill根>/venv/bin/python <skill根>/scripts/login_1688.py`（路径由 `__file__` 自动推断，不写死机器）
- `scripts/verify_login.py` — 验首页 + 详情页登录态是否生效。
- `scripts/verify_endpoints.py` — 诊断用，复现"搜索页踢回 / 详情页免墙"差异。

### 重登录流程（cookie 过期/清缓存后）
1. 确认 MCP 独立 Chromium 的 `drission_user_data` 存在（`<skill根>/venv/drission_user_data/`）。
2. 清旧登录态（如需）：`rm -rf <skill根>/venv/drission_user_data`（会丢全部 MCP 浏览器登录态，谨慎）。
3. 跑 `scripts/login_1688.py` → 用户扫 `/tmp/1688_qr_login.png` 二维码。
4. 跑 `scripts/verify_login.py` 确认 `BLOCKED False`。
5. 之后 MCP `get_product_detail_and_price` 即可用；搜索仍用方案0。

## 可分发打包（2026-08-20 实战，已验证可转其他 Hermes 实例）
本 skill 已做成**可 `cp -R` 分发**的版本（见 `~/Desktop/1688-sourcing-skill/` + `.tar.gz`）。通用做法见 `references/distributable_skill_packaging.md`。要点：
- **MCP 本体收进 skill**：`mcp/` 子目录放 `server.py`/`bootstrap.py`/`requirements.txt`，不再依赖外部裸 repo。
- **路径全相对化**：Python 脚本用 `HERE=os.path.dirname(os.path.abspath(__file__)); SKILL_ROOT=os.path.dirname(HERE)` 推断；AppleScript 用 `POSIX path of (path to me)` + `dirname` 推断。**绝不在脚本里写死 `/Users/xxx` 或 `/home/xxx`**（会导致换机器全断）。
- **隔离 venv 随 skill 走**：venv 建在 `<skill根>/venv/`，`bootstrap.py` 清 Hermes 注入的 `PYTHONPATH` 后强制用 venv 的 site-packages。
- **写 `setup.sh`**：一键建 venv + 装依赖 + 打印 `hermes config set mcp_servers...` 命令。
- **登录态/凭证绝不随包走**：`drission_user_data`（含账号登录态）是绑定账号+设备的，硬塞进包只会污染对方，**打包前务必排除**，对方自己扫码登录。
- **收尾校验**：`grep -rn "/Users/aimac" .` 应零残留；换一个假 `__file__` 路径 exec 验证 `USER_DATA` 跟着变。

## 找品主驱动（参数化，替所有 `*_2020.scpt` 写死副本）
- `scripts/run_search.scpt` — 改文件头 4 个常量（`DIM`/`CARTON`/`PROV`/`PAGES`）即可复用任意任务：构造 GBK 编码搜索 URL → 真 Chrome 翻页+滚动懒加载 → 抓 offerId 落 `/tmp/1688_run_result.txt`。复用 `extract_ids.js`。（路径已相对化，坑24 分发铁律）
- **`scripts/drive_playwright.js` —【推荐】Playwright 版主驱动**（2026-08-21 收编 + 能力升级）：`chromium.connectOverCDP('http://127.0.0.1:9222')` 驱动真实登录态 Chrome + 首页暖场 + 组合提取 + 复用 verify_carton.js/price_clean3.js 实时复核。四大升级：
  1. **双记号精确搜索**：同时搜 `DIM` 与 `DIM.replace('*','x')`，合并去重，逼近真立方体（坑29：1688 搜 `*` 是模糊匹配，含某维度 16cm 全排进池；`x` 才是精确立方体）。
  2. **CDP 健康自检**：开头先探 9222，挂了**不擅自拉起**（遵守"手动拉起"约束），打印精确启动命令让你执行。
  3. **持久化已验商品库**：验证过的商品写入 `<skill>/store/verified.json`（按 DIM 分桶），下次同 DIM 任务**自动跳过已验 ID**只补新出现，并按单价升序汇总全部历史命中。
  4. **自动渲染 markdown 报告**：跑完写 `<skill>/store/<DIM>_<PROV>_report.md`，无需手动转。
  - 环境变量：`DIM`/`CARTON`/`PROV`/`PAGES`/`STOP_HIT`(0=验全部)/`KNOWN`/`CDP`/`OUT`。例：`DIM=17.5*17.5*8.5 CARTON=纸箱 PAGES=5 node scripts/drive_playwright.js`。
  - 运行方式（坑28）：`cd scripts && NODE_PATH=/Users/aimac/.hermes/1688-pw/node_modules node ./drive_playwright.js`（playwright 装在 1688-pw 的 node_modules，用 NODE_PATH 指向它）。
- 拿到 ID 后：规格核对用 `check_spec.js`（注入 `window.TARGET`），品类过滤（排礼盒）用 `verify_carton.js`，价格提取用 `price_clean2.js`。三件套均参数化，勿内联。**矩阵式尺寸（长宽×高写法，坑30）一律用 `verify_carton_matrix.js` 替代 `verify_carton.js`**——它同时覆盖连写与矩阵两种写法，不会有漏检。
- 搜索阶段若目标可能是矩阵式彩盒（常见全尺寸定制），**搜索词必须加「彩盒定制」**（坑31）：`KW=8*8*9cm纸盒,彩盒定制` 两词合并。`drive_playwright.js` 的 `KW` 环境变量逗号分隔多词即生效。
- 旧 `*_2020.scpt` 为 20*20*10cm 任务实战副本，**已弃用**，新任务一律用 `run_search.scpt` 或 `drive_playwright.js`。
