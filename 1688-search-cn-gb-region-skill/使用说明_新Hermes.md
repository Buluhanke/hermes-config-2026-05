# 1688 找品 Skill —— 使用说明（给新 Hermes / 接手 Agent 读）

> 这是一套**驱动用户本机已登录的 Google Chrome** 在 1688 上找货的能力。核心是「真实浏览器 + AppleScript 注入 JS」绕开 1688 反爬，不是 API、不是无头爬虫。

---

## 0. 前置条件（必须满足，否则整套不可用）
1. macOS，已装 Google Chrome（路径 `/Applications/Google Chrome.app`）。
2. Chrome 已登录 1688 账号（诚信通/采购号均可），有搜索和详情页访问权限。
3. Hermes 运行环境能调 `osascript`（AppleScript）驱动 Chrome —— 即**本机**执行，不是远程无头。
4. 不需要任何代理、不需要 API key、不需要企业认证。

> 若 Chrome 未登录：先让用户打开 Chrome 登 1688，再回来跑。不要自己起无头/调试端口实例（会被风控，且违反用户约定）。

---

## 1. 这套能力解决什么
输入：「关键词 + 尺寸 + 地区」→ 输出：「真实在售、规格命中的货源 + 精确单价/库存 + 供应商」。
例：`16*16*16cm 纸箱，江浙沪` → 4 个真纸箱、各自 16×16×16 的单价与库存。

端到端 6 步（见 SKILL.md 详情）：
- Step1 搜：改 `run_search.scpt` 的 `DIM`/`PROVINCE`/`PAGES` → 跑 → 抓 offerId 列表
- Step2 去重：python 对 offerId 去重
- Step3 规格复核：`verify_carton.js` 注入详情页，按「真实 SKU 尺寸集合」判是否真有该尺寸（**关键：不靠广告文案**）
- Step4 价格：`price_clean3.js` 注入详情页，抠目标尺寸的精确单价+库存
- Step5 比价：表格化
- Step6 交付：给用户 supplier + 价格 + 起批

---

## 2. 直接复用的命令（改关键词就跑）
```bash
# ① 搜（改 DIM / PROVINCE / PAGES 三处）
#   文件：scripts/run_search.scpt
osascript scripts/run_search.scpt
#   → 产物 /tmp/1688_<关键词>_result.txt（GBK，python 解码）

# ② 去重拿 ID 列表
python3 -c "..."

# ③ 规格复核（改 TARGET 尺寸）
#   文件：scripts/check_batch_optimized.scpt
osascript scripts/check_batch_optimized.scpt
#   → 产物 /tmp/check_*.txt（isCarton:true 即命中）

# ④ 精确价（改 TARGET 尺寸）
#   文件：scripts/price_clean3.js 由驱动脚本调用
```

**最少改动**：`run_search.scpt` 里 `property DIM : "16*16*16"` 改关键词；驱动脚本里 `window.TARGET='16*16*16'` 改目标尺寸。其余不动。

---

## 3. 新手必读陷阱（完整 23 条在 SKILL.md，最高频 8 条）
1. 搜索端点**只用** `s.1688.com/selloffer/offer_search.htm`，禁 `s/1688search`、禁 `location=` 跳转——后者必弹登录墙。
2. 关键词必须 **GBK 编码**（`16%2A16%2A16cm%D6%BD%CF%E4`），UTF-8 直接拼会空搜/乱码。
3. 抓 ID 从 `outerHTML` 解析 `data-offer-id`，不要只取 `a.href`。
4. 列表页**懒加载**：每个 tab 滚动 8 次再抓，否则漏半页。
5. 规格命中**唯一权威 = 详情页 `.module-od-sku-selection` 的 DOM 文本**，绝不并内嵌 `<script>`（script 含跨商品广告尺寸 → 假阳性）。
6. AppleScript 写文件**别用 `open for access`**（报 `-39` 且截断续跑），一律 `do shell script "printf >>"` 追加。
7. 降速：批量每批 3 个、间隔 8 秒，防验证码；支持断点续跑（读已验 ID 跳过）。
8. 中文回传一律走 `esc()` 转 `\uXXXX` ASCII 通道，python 侧 `unicode_escape` 解码——否则 AppleScript 桥接中文乱码。

**写 JS 注入脚本专用坑（坑22）**：正则里**绝不用 `\d \s \.`**，`write_file`/heredoc 会把 `\` 双写导致正则失效。改 `[0-9]` / `[ ]` / `[.]`。

---

## 4. 验证（每次大改后必做）
- `node --check scripts/*.js` 验语法（**注意**：只验语法不验正则语义，正则 bug 它发现不了，需实跑）。
- 真实浏览器跑一遍 16×16×16：预期 4 真 1 假（`751990874462` 必为 False，它的 SKU 无 16×16×16）。
- 若 `skuHit` 全 False 但页面确有尺寸 → 95% 是正则被双写（坑22）。

---

## 5. 已知边界（别硬刚）
- 1688 官方开放平台 API：需企业营业执照+中国 IP 白名单，本机个人账号拿不到，不适用。
- mtop `queryofferskuselectormodel`：需 `_m_h5_tk` 签名 + 跨域，浏览器内 XHR 被 CORS 拦，拿不到干净 JSON。
- 搜索端点风控是 1688 服务端行为，只能靠「真实登录态 + 降速」规避，没有代码层绕过。
- 详情页价格有 inline 和 size-bar 两种布局，`price_clean3.js` 两种都覆盖。

---

## 6. 文件地图
```
1688-search-cn-gb-region-skill/
├── SKILL.md                      # 主文档：流程 + 23 条陷阱 + 实战样例
├── scripts/
│   ├── run_search.scpt           # 搜索+抓ID驱动（改 DIM/PROVINCE/PAGES）
│   ├── check_batch_optimized.scpt# 规格复核驱动（断点续跑+shell IO+窗口守卫）
│   ├── verify_carton.js          # 规格命中（真实SKU尺寸权威+品类放宽）
│   ├── price_clean3.js           # 精确单价+库存（inline/size-bar双布局）
│   ├── extract_ids.js            # 列表页抽 offerId
│   ├── check_spec.js / price_table.js / price_extract.js / price_clean.js / price_clean2.js  # 历史/备选实现
│   └── *.py                      # 登录态校验等辅助
└── references/                   # 调研记录、MCP接入、打包说明（备查，非必读）
```

接手时：**先读 SKILL.md 全文**，再照 Step1-6 跑一遍 16×16×16 验证环境是否健康。
