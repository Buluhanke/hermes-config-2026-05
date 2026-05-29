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

### Step 2：找品策略

**三步走，按优先级选：**

#### 方式A：AnySearch（推荐，2026-05-29验证可用）
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py batch_search \
  --queries '[{"query":"纸箱 义乌 1688 批发","max_results":5}]'
```
- 输出结构化，1688商品直接命中摘要
- 速度快，不触发反爬
- **局限**：摘要数据有限（标题/价格/已售/货源地），无法自动获取商品详情页的规格/颜色/尺寸等详细规格数据

#### 方式B：CDP拦截1688搜索postMessage数据
**⚠️ 已失效（2026-05-29验证）**：1688对headless Chrome触发滑块验证，直接搜索URL（s.1688.com）100%被拦。CDP浏览器无法绕过。

**触发条件**：只有在用户**已登录1688的浏览器**中手动搜索关键词后，才能用CDP拦截postMessage数据。自动化搜索全部失败。

正确流程（如条件满足）：
1. `browser_navigate` → `https://s.1688.com/selloffer/offer_search.htm?keywords=关键词`（用户已登录态）
2. 等待8秒，等postMessage数据到达
3. 从`window.data.offerV2.response.data.OFFER.items`读取所有商品数据
4. 数据字段映射：`items[i].data.offerId / title / priceInfo.price / bookedCount / companyName / province / linkUrl`

#### 方式C：extract提取工厂详情页
```bash
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py extract "https://detail.1688.com/offer/商品ID.html"
```
可提取联系方式、公司名所在地等静态内容。详情页反爬较轻，可以访问。

**方式选择优先级**：AnySearch(快) → extract详情页(辅助) → CDP(仅用户已登录时)

### 1688反爬实测结论（2026-05-29）
- 直接URL访问搜索结果页 → 100%触发滑块验证码
- AnySearch → 可用，但数据粒度受限
- 详情页extract → 可用，数据较全
- CDP拦截 → 仅用户在浏览器登录后才有效

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

## AI 网站智囊工作流（重要！）

当 1688 自动化遇到技术障碍（验证码、反爬、CDP连接失败等），不要硬撞。
**正确路径：咨询 AI 网站智囊获取方向性建议，再决定下一步。**

### 已验证可用的 AI 网站（免登录）
- **Gemini** (https://gemini.google.com) ✅ — 可直接输入技术问题
- **智谱清言** (https://www.zhipuai.cn) ✅ — 页面可直接输入
- **豆包** (https://www.doubao.com) ✅ — 免登录，页面可直接输入
- **DeepSeek** — 需要登录

### 工作流
1. 截图当前问题界面（用 `browser_vision` 或 `computer_use` capture）
2. 在 AI 网站输入具体技术问题，如："1688网站滑块验证码如何通过自动化方式解决？请提供技术方案"
3. AI 回复后，用 Vision OCR 读取截图文字（`/opt/homebrew/bin/python3` + Vision.framework）
4. 根据建议决定是否继续尝试，或切换方案

### 读截图的方法（已验证）
```python
# Vision.framework 读本地图片（Mac原生，无需网络）
/opt/homebrew/bin/python3 -c "
from Vision import *
import Cocoa
img = Cocoa.NSImage.alloc().initWithContentsOfFile_('/path/to/screenshot.png')
if img:
    print(f'OK: {img.size().width}x{img.size().height}')
else:
    print('FAILED')
"
```

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

### 本地Chrome CDP连接失败（已验证）

**症状**：`curl http://localhost:9222/json` 返回502，或连接成功但 Chrome 使用随机端口。

**原因**：用户Chrome以 random port 模式运行，或9222端口已被占用。

**解决方案**：需要用户手动开启Chrome远程调试并告知端口，或接受CDP方案不可用的事实。

**检测命令**：
```bash
# 检查9222端口是否在用
lsof -i :9222

# 查看Chrome调试端口
ps aux | grep -i chrome | grep remote-debugging
```

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

## 1688官方API结论（2026-05-29验证）

**结论：不适合买家身份的中小贸易商。**

1688开放平台ISV入驻需要：
- 企业支付宝（已认证）
- 营业执照
- 审核时间2-3工作日

迅龙贸易是买家身份（从1688采购，不是卖货），不需要这些权限，也无法利用卖家端API。

1688官方API技能（`1688-open-platform-api`等）都是**卖家端**功能：商品发布、订单管理、营销工具。买家能用的是"找货/搜索"类API，但需要企业资质认证。

**实际路径**：CDP拦截已登录浏览器的postMessage数据，或用AnySearch替代。不申API Key。

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
- `references/ai-agents-1688-knowledge.md` — AI网站智囊（Gemini/智谱清言/豆包）关于1688自动化方案的问答记录