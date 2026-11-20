# 1688 找品：搜索框定位 + Chrome 输入的坑（2026-08-19 实测）

## 坑1：地址栏 ≠ 1688 站内搜索框（用户纠正过）

现象：在 Chrome 顶部「地址和搜索栏」输入 `16*16*16cm纸箱` 回车，跳到 **Google 搜索结果页**，不是 1688 站内搜索。用户原话：「你16*16*16cm纸箱输入不在1688的搜索页面里」。

根因：Chrome 的地址栏默认是 Google 搜索引擎，回车=网页搜索，与 1688 无关。

**正确做法（顺序）**：
1. **点进 1688 页面内搜索框再输入（唯一可靠）**：1688 首页/结果页有独立站内搜索框（AXTextField，结果页 bounds 约 `[502,292,735,48]`，placeholder 是搜索词或「纸箱半高」）。`click` 该元素 → `type`（foreground）→ `key return` 才进 1688 结果页（URL 带 `spm=...searchbox.0`）。
2. **油猴脚本**：仅用于翻页批量提取，不解决搜索入口问题。

⚠️ **`?keywords=` URL 导航是陷阱，不是兜底**：`https://s.1688.com/s/1688search?keywords=...` 会被 1688 **重定向上清参数**成 `offer_search.html`（无关键词），结果变空搜 → 出鞋/工艺品/无纺布袋等乱品。UTF-8 或 GBK 编码都救不了（根因是重定向，非编码）。曾因此被用户纠正「搜索的不是纸箱」。

验证：结果页 `document.title` 含搜索词 **且** 搜索框 `.value` 等于搜索词，才算真搜成功；若 title 是「批发_供应_阿里巴巴」但搜索框空 = 失败重来。

## 坑2：多窗口 Chrome 的 type/key 必须 foreground

现象：Chrome 开 2+ window 时，后台 `type`/`key` 被拒，报 `same_pid_keyboard_ambiguity`（pid 拥有多个 eligible window，无法确认打到哪个）。

正确做法：`computer_use` 的 `type`/`key` 加 `delivery_mode="foreground"`。会短暂把目标窗口提到前台输入再还原，验证可靠。
`click` 用 `element` 索引通常不受此限（走 accessibility 路由）；仅进程级键盘事件需 foreground。

## 坑3：详情页规格不靠 CDP JS，直接 parse AX 元素 JSON

`computer_use capture` 成功时把完整元素树写入 `~/.hermes/cache/computer_use/elements_<hash>.json`（路径在 capture 返回的 `elements_file` 字段）。

用 `search_files` 在该 JSON 搜规格词即可抠出 SKU 全表，无需油猴/JS：
- 搜 `16X16X16cm`、`内径`、`规格型号`、`¥`
- 实测命中（第一个商品即命中需求）：
  `"16X16X16cm 内径15.5X15.5X15.3高 126g"`（特硬覆膜白盒 & 特硬牛皮盒两种材质）
  主价格区 `¥1.61`（y≈569 顶部价格块）

比油猴脚本更稳：纯 AX 树文本匹配，绕开「Chrome 双进程陷阱」里 CDP JS 返回空的问题。
