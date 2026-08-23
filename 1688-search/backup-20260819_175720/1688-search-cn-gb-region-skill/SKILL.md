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
- `references/spec_formats.md` — 1688 规格写法实测样本（连写/拆写/大小写）

## 已验证样例（实战跑通，可直接复用）
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
- 搜索 URL：同构，`keywords=16*16*16cm%D6%BD%CF%E4`
- 已知命中：`727704740601`（浦江联恒/浙江金华）、`751990874462`（慈溪/浙江）
- 用户给过的相关链接（江浙沪搜索结果内）：`680682547475`、`634987797003`、`634522031289`

## 备注
- 视觉通道（vision_analyze）本机可能 404（venv 污染 PIL）；本 skill 全程依赖 DOM 文字通道，不依赖视觉
- 用户确认的已知正确商品可先列入清单，再补亲验
- 脚本路径：`scripts/extract_offers.scpt`、`scripts/check_spec.js`（参数化 TARGET）、`scripts/check_batch.scpt`；改尺寸只动 `check_batch.scpt` 顶部 `property TARGET`
