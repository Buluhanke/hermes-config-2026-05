# 1688 技能联动地图（2026-05-29）

## 当前采购工作流

```
用户："找纸箱供应商"
  ↓
anysearch 批量搜 → extract工厂联系方式
  ↓
1688-sourcing → CDP拿1688真实数据 → 5家比价
  ↓
decision-helper → 量化评估选哪家
  ↓
hindsight 记住这次决策（含经验叙事）
  ↓
hermes-ocr → 读资质文件/报价单截图
```

## 技能状态

| 技能 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `1688-sourcing` | `procurement/1688-sourcing/` | ✅ 可用 | CDP拦截法，无需AK |
| `1688-search-data-extract` | `procurement/1688-search-data-extract/` | ✅ 可用 | 1688-sourcing底层依赖 |
| `anysearch` | - | ✅ 可用 | 批量搜+extract，匿名 |
| `decision-helper` | `decision/decision-helper/` | ✅ 可用 | 框架工具，无需key |
| `hindsight` | 插件 memory/hindsight | ✅ 已集成 | Docker+ollama，observations模式 |
| `hermes-ocr` | `vision/hermes-ocr/` | ✅ 可用 | 5引擎自动降级 |

## 需要AK但暂不需要的技能

这些skill需要1688企业API Key（企业支付宝+营业执照认证），作为买家暂时用不上：

- `1688-source-suppliers` — 需AK，找供应商（CDP方案已够）
- `1688-shopkeeper` — 需AK，店铺管理（非卖家角色）
- `1688-item-select` — 需AK，重点品圈选（非卖家角色）
- `1688-product-analysis` — 需AK，商品分析（非卖家角色）
- `1688-shop-health-check` — 需AK，店铺诊断（非卖家角色）

**结论：** CDP方案够用，暂不申请1688开放平台API。

## 1688开放平台申请条件（备查）

- 企业支付宝账号（必须）
- 营业执照认证
- 需审核1-3天
- 适合：有自己的1688店铺需要管理的卖家
- 不适合：纯买家（找货源、比价）