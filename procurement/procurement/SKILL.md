---
name: procurement
description: 采购管理入口 skill — 整合 1688 货源/供应商管理/议价/质量控制/合同/库存/物流的全链路采购能力。**核心定位**：老板说需求 → Hermes 执行采购全流程 → 闭环交付。**沟通铁律**：不要主动提 1688/找品，除非用户先提。
version: 1.0.0
author: Hermes Agent
triggers:
  - 老板发来采购需求
  - 需要找供应商比价
  - 需要跟供应商议价
  - 需要下单/跟单/物流跟踪
  - 采购合同/质量/库存问题
---

# Procurement — 采购管理全链路

## 定位

**老板说需求 → 执行全流程 → 闭环交付**

所有采购相关 sub-skill 都归属本 umbrella，通过 `skill_view(name)` 调用具体 skill。

## Sub-skills（通过 `skill_view` 调用）

| Sub-skill | 用途 |
|-----------|------|
| `1688-automation-flow` | 1688 找品/下单/跟单全流程 |
| `1688-price-negotiation` | 供应商议价话术模板 |
| `supplier-relationship` | 供应商分层维护/关系管理 |
| `quality-control` | 来料检验/问题分级/退货 |
| `contract-management` | 采购合同条款清单 |
| `inventory-early-warning` | 安全库存/四色预警 |
| `shipping-tracking` | 物流跟踪 |
| `seasonal-strategy` | 季节性采购策略 |

## 沟通铁律

**不要主动提 1688/找品/货源，除非用户先提。**

用户已明确表示对采购/1688 方向不感兴趣（"找品这事不要再提了"）。所有采购操作在后台执行，不主动汇报进度，除非用户问。

## 历史说明

原 `pro-buyer` skill 已废弃，内容合并至本 umbrella。如果 cron job 仍引用 `pro-buyer`，需改为引用 `procurement`。

## 触发判断

当用户提到采购相关词（"找"、"买"、"供应商"、"价格"、"下单"等）时，先判断是哪种场景，再调对应 sub-skill。
