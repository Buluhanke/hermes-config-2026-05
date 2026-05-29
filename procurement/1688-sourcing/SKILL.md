---
name: 1688-sourcing
description: >
  1688 采购找品标准化流程。浙江/江浙沪皖货源地筛选，5家供应商比价，
  结构化汇报。不需要定制服务，不需要工厂性质，不需要跨境出口标签。
triggers:
  - 1688找品 / 1688采购 / 找供应商 / 对比价格
  - 气泡袋 / 纸箱 / 包装材料 / 快递袋 / 气泡膜
  - 帮我找XX供应商 / 哪家便宜 / XX哪里有卖
category: procurement
---

# 1688 采购找品标准化流程

## 核心原则

**汇报格式（固定，不要变）：**
```
找到N家供应商：
1. 供应商名 ¥价格 - 备注
2. 供应商名 ¥价格 - 备注
...

建议第X家，性价比最高。需要我先联系询价吗？
```

**不许出现的内容（用户明确不要）：**
- ❌ "定制"相关（用户不需要定制服务）
- ❌ 工厂性质/经营模式列
- ❌ "支持跨境出口亚马逊"/"支持亚马逊/东南亚"列
- ❌ 复杂表格、多级表头
- ❌ 价格区间写成"¥5.2~¥5.8" → 写成"¥5.2"

**用户固定要求：**
- 货源地：浙江金华优先，扩大到江浙沪皖
- 数量：5家对比
- 供应商：只要卖家（不限工厂/贸易/商行）
- 格式：简单4列（供应商 | 价格 | 已售 | 起批/备注）

## 工作流程

### Step 1：确定关键词
用户说"搜XX" → 立即确认关键词 → 执行

### Step 2：找品策略（重大更新 2026-05-29）

**三步走，任选其一：**

#### 方式A：AnySearch（推荐，最快）
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py batch_search \
  --queries '[{"query":"纸箱 义乌 1688 批发","max_results":5}]'
```
输出结构化，1688商品直接命中。注意：1688搜索结果页JS渲染，extract可能拿不到数据，但search本身能返回摘要。

#### 方式B：CDP拦截1688搜索postMessage数据（数据最准确）
1688搜索结果页（s.1688.com）数据通过`window.postMessage`从父窗口注入，DOM中不直接渲染。
正确流程：

1. `browser_navigate` → `https://s.1688.com/selloffer/offer_search.htm?keywords=关键词`（CDP浏览器，已登录态）
2. 等待8秒，等postMessage数据到达
3. 从`window.data.offerV2.response.data.OFFER.items`读取所有商品数据
4. 数据字段映射：`items[i].data.offerId / title / priceInfo.price / bookedCount / companyName / province / linkUrl`

**示例代码（CDP Python）：**
```python
import urllib.request, json, websocket, time

req = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
tabs = json.loads(req.read())
t = tabs[-1]  # 最新标签
ws = websocket.create_connection(t['webSocketDebuggerUrl'], timeout=15, suppress_origin=True)
mid = [1]
def sv(m, p=None):
    ws.send(json.dumps({"id": mid[0], "method": m, "params": p or {}}))
    r = json.loads(ws.recv())
    mid[0] += 1
    return r

sv("Page.navigate", {"url": "https://s.1688.com/selloffer/offer_search.htm?keywords=关键词"})
time.sleep(8)

# 重新连接（导航后websocket可能断开）
ws.close()
req2 = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
tabs2 = json.loads(req2.read())
t2 = tabs2[-1]
ws2 = websocket.create_connection(t2['webSocketDebuggerUrl'], timeout=15, suppress_origin=True)

# 等待数据
for _ in range(8):
    r = sv("Runtime.evaluate", {"expression": "window.data?.offerV2?.response?.data?.OFFER?.items?.length || 'waiting'", "returnByValue": True})
    if r.get('result',{}).get('result',{}).get('value','') > 0:
        break
    time.sleep(1.5)

# 提取所有商品
r = sv("Runtime.evaluate", {"expression": """
(function(){
  var items = window.data.offerV2.response.data.OFFER.items;
  var out = [];
  for(var i=0; i<items.length; i++){
    var d = items[i].data || items[i];
    out.push({
      offerId: d.offerId,
      title: (d.title||'').replace(/<[^>]+>/g,''),
      price: (d.priceInfo||{}).price||'',
      priceUnit: (d.priceInfo||{}).unit||'',
      sold: d.bookedCount||'',
      comp: d.companyName||d.loginId||'',
      loc: d.province||'',
      city: d.city||'',
      href: (d.linkUrl||'').replace('http://','https://')
    });
  }
  return JSON.stringify(out);
})()
""", "returnByValue": True})
```

#### 方式C：extract提取工厂详情页（适合拿到商品链接后查资质）
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py extract "https://detail.1688.com/offer/商品ID.html"
```
可提取联系方式、公司名所在地等静态内容。搜索结果页（JS渲染）extract效果差，详情页效果好。

**方式选择优先级**：AnySearch(快) → CDP(准) → extract(辅助)

### Step 3：筛选江浙沪

从提取的items中筛选：
```python
jiangzhe = [it for it in items if it['loc'] in ['浙江','江苏','上海','安徽'] and '气泡' in it['title']]
```

### Step 4：汇报

找到5家供应商后，汇报格式：
```
浙江气泡袋供应商对比（货源地：江浙皖）：

| # | 供应商 | 价格 | 已售 | 起批 |
|---|---|---|---|---|
| 1 | 义乌市念想包装 | ¥0.1/个 | 7.5万+个 | 1个起 |
| 2 | 金华市柯典包装 | ¥0.2/个 | 4万+个 | 1个起 |
| ... | ... | ... | ... | ... |

建议第1家，价格最低已售最高。询价吗？
```

### Step 5：询价（如用户确认）

使用 `email-drafter` skill 起草询价邮件。

## 货源地优先级

1. **浙江金华** — 首选（工厂集中，价格低）
2. **浙江（非金华）** — 杭州、温州、宁波、义乌
3. **江苏/上海/安徽** — 扩大搜索时包含

## 常见品类货源地规律

| 品类 | 主要货源地 |
|------|---------|
| 气泡袋/气泡膜 | 浙江金华、广东东莞 |
| 纸箱/飞机盒 | 浙江义乌、江苏 |
| 快递袋/塑料袋 | 浙江、广东 |
| 包装辅材 | 浙江、江苏 |

## 关键陷阱

### ClawHub社区技能安全扫描规则（重要！）

**症状**：`hermes skills install` 报 "BLOCKED — community source + dangerous verdict"

**原因**：Hermes安全扫描对community源skill有3级判定：
- `SAFE` → 直接安装
- `CAUTION` → 可用 `--force` 强制安装
- `DANGEROUS` → `--force` 也无法安装（通常是需要外部API密钥）

1688相关技能大多标记为 DANGEROUS（因为需要 `ALI1688_APP_KEY` 等密钥存放在环境变量，被扫描识别为"凭证泄露风险"）。这是误报，解决方法是先配置好密钥再安装。

**正确流程**：
1. 在 `~/.hermes/.env` 配置好 `ALI1688_APP_KEY=...` 等
2. 再执行 `hermes skills install clawhub/1688-product-search --yes`
3. 如果还是DANGEROUS，只能等官方修复扫描规则

### 1688搜索URL反爬（最常见失败原因）

**症状**：访问 `s.1688.com/company/search.html?keyword=XX` 返回滑块验证页面。

**解决方案**：永远不要直接访问搜索结果URL。用1688首页搜索框输入关键词。

### 1688价格提取

详情页价格是**阶梯价**，正则 `¥[\d.]+` 会匹配所有价格阶梯。只取第1个（起批量价格）：
```python
price = (text.match(/¥[\d.]+/g) || []).slice(0,1).join(' / ')
```

### 50*25cm等非标准尺寸

**问题**：大多数品类没有50*25cm这种非标准规格，搜索"气泡袋 50*25cm"结果里全是其他尺寸。

**正确做法**：
1. 搜索更大范围关键词（如"气泡袋"），提取所有结果
2. 从结果中筛选**接近尺寸**（如20×25、25×30等）
3. 如果没有接近尺寸 → 告知用户需要定制，报价通常比标准规格贵30-50%
4. 也可以用艺诺包装源头厂家（ID:808613438216）这类有"多规格可选"标题的供应商，询问是否有50*25

**50*25cm可直接推荐的供应商**：
- 金华翼美包装（ID:903586941684）：20×25cm ¥5/件，已售43
- 艺诺包装源头厂家（ID:808613438216）：多规格（10~30cm都有），¥0.11/件起，已售329 — **问这家有没有50*25**
- wutao19860806（ID:623635256786）：25*30cm ¥0.12/件，已售149

## 1688官方API技能（需1688开放平台企业资质）

如已申请1688开放平台API Key，可在 `~/.hermes/.env` 配置后使用：
- `clawhub/1688-product-search` — 官方API搜索
- `clawhub/1688-product-find` — 以图搜货

个人买家身份难以申请，建议优先用CDP postMessage法。

## 技能联动工作流

```
anysearch（批量搜索）→ 1688-sourcing（比价流程）→ decision-helper（决策评估）
                                        ↓
hindsight（记住决策）← 每次采购完成后自动存入
                                        ↓
hermes-ocr（辅助）← extract工厂资质文件 / 读报价单截图
```

**AnySearch常用命令**（runtime.conf已配置python3）：
```bash
# 单次搜索
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py search "关键词" --max_results 5

# 批量搜索（推荐，比单次快）
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py batch_search \
  --queries '[{"query":"纸箱 义乌 工厂","max_results":5},{"query":"气泡袋 金华 批发","max_results":5}]'

# 全页内容提取（工厂详情页）
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py extract "https://detail.1688.com/offer/ID.html"
```

**1688 ClawHub技能库（2026-05-29新增）

已安装以下ClawHub技能，可直接调用：

| 技能 | 用途 |
|------|------|
| `1688-sourcing-agent` | 采购全流程 |
| `1688-procurement-agent` | 采购教练 |
| `1688-price-monitor` | 监控批发价 |
| `1688-source-suppliers` | 找供应商 |
| `1688-shop-health-check` | 店铺诊断 |
| `1688-finance-tax` | 税负测算 |

**安全扫描规则**：community源skill被标记为dangerous的无法安装（即使--force也不行）。被标记为caution的可用--force强制安装。

- `email-drafter` — 询价邮件起草
- `hermes-rpa` — CDP浏览器自动化底层
- `1688-open-platform-api` — 官方API（需企业资质，不适合纯买家）
- `references/1688-search-postmessage.md` — 搜索数据postMessage拦截法的完整技术细节和数据结构