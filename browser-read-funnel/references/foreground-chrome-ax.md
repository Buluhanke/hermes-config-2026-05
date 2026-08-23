# 前台 Chrome AX 树读取（L1，登录态真实页主路径）

## 何时用
- 目标页面在**用户前台真实 Chrome** 窗口里（含登录态：1688、淘宝、钉钉、企业后台等）。
- 用户铁律：**禁用调试端口(9222)、禁用另起 Chrome 实例、优先真实登录态**。
- 这条路**完全绕过 9222**（即使 `/json` 返回 404 也能读），是合规的 L1 主路径。

## 调用（Cua Driver 0.17）
```
computer_use(
  action='capture',
  app='Google Chrome',   # 不填则抓最前窗口；填了只抓 Chrome
  mode='ax'              # 只要无障碍树文本，不要截图。som 模式用于找可点元素
)
```
返回 `elements` 数组 + `elements_file`（如
`/Users/aimac/.hermes/cache/computer_use/elements_<hash>.json`）。
AX 树节点数通常 600~1200，够读出标题/价格/规格/SKU 全表。

## 坐标缩放（点击必看）
- AX `bounds` 是 **native 桌面坐标**（可达 ~1920×1025），**不是**截图像素（约 1456×755）。
- 估算 scale ≈ **1.36**（= native / screenshot）。
- 点击用 `coordinate = [native_x / 1.36, native_y / 1.36]`。
  - 例：商品图 native 中心 (394, 923) → 传 `[290, 679]`。
- Cua Driver 0.17 **拒绝裸 `element_index`**（报错 `snapshot_id_required`）。要么传缩放后的 `coordinate`，要么用 `set_value` 选下拉。

## click 返回 `unverifiable` 是假阴性
- 现象：`effect: "unverifiable"`，消息 “PX hit-test pressed the background element via AX”。
- 原因：`capture_after=true` 在页面跳转**完成前**拍照，所以看起来没变。
- 处理：**重新 `capture(mode='ax')` 一次**，看 window_title / 关键 label 是否变化即可确认跳转。**不要重试点击**，也不要降级到截图。

## 解析 AX 树
- 详情页节点上千，手读困难 → 用 `scripts/parse_ax_tree.py` 解析 `elements_file`：
  ```
  python3 scripts/parse_ax_tree.py <elements_json> --keys "规格,材质,厚度,尺寸,价格,起订" --context 6
  ```
- 脚本逻辑：对每个命中关键词的节点，抓它及之后若干个非空 label，重建成「字段→值」相邻结构，去重后输出。能从 SKU 矩阵、件重尺表里挖出全部值。

## 实证（2026-08-22，1688 登录态搜索页）
URL：`https://s.1688.com/selloffer/offer_search.htm?keywords=16*16*16cm纸箱`
1. `capture(ax)` 读前台搜索页 → 零截图读出 14 个商品（标题/价格/销量/供应商）。
2. 坐标点击第 1 名商品图 → 重抓 AX 确认跳进详情页。
3. `parse_ax_tree.py` 挖详情页：材质瓦楞纸板、厚度 0.4~0.7、棕黄色、超硬、江苏产；
   SKU 矩阵 40+ 尺寸（含半高箱，如 `25*25*25CM`、`1号(53*29*37CM)`）；
   件重尺表（长×宽×高×体积×重量，如 `13号(13*8*4.5CM)→27×21×0.50`）。

### 关键认知（用户早先指出，真读才印证）
1688 会把搜索词**语义扩展**——搜 `16*16*16cm纸箱` 结果全是「快递箱/五层特硬」，标题里根本没有 16*16*16cm。只有真登录态读出来才能发现，web_search 猜不到。这也是为什么 1688 找品必须走真实 Chrome 登录态，不猜 URL。

## 边界
- ✅ 随时：前台 Chrome 里**任意**打开的页面（含登录态）。
- ⏸️ 无前台窗口的纯后台/无头登录页 → 仍走 A2（`scripts/curl_xhr.py --cookie`）。
- ❌ Canvas/WebGL 纯像素 → 才降级截图 OCR（且 vision_analyze 对本机 PNG 常失效，失效一次即放弃）。
