---
name: 1688-price-extraction
description: 1688精准价格提取 — 用CDP+browser_console拿登录态页面真实价格，与curl/API方案对比。
trigger: 1688 价格 对比 找品 规格价格
---

# 1688 Precision Price Extraction

## Trigger
User wants 1688 product prices matching what they see in Chrome (logged-in tiered/client prices).

## Core Problem
- `1688-cli` returns "unlogged-in default price" — different from logged-in tiered/client prices
- 1688 is pure JS render; curl gets near-empty HTML
- Prices hidden in dynamic components; innerText can't find them

## Workflow

### Step 1: User sets filters in Chrome
Province (Jinagsu/Zhejiang/Jinhua/Yiwu) + keyword + specs. Notify agent when ready.

### Step 2: Get offerId list
Two options:
- **CDP direct**: Run JS on Chrome search results page to extract all offerIds
- **1688-cli**: `python3 findchain.py "keyword" --max 20` (province filter may be inaccurate — verify manually)

### Step 3: CDP extract precise price (core)
Use `browser_navigate` to open product page, then `browser_console` with JS:

```js
// Click spec button
(function(){
    var btns = document.querySelectorAll('button');
    for(var b of btns){ if(b.innerText.trim() === '16*16*16cm'){ b.click(); return 'ok'; } }
    return 'not found';
})()

// Extract price (after clicking spec)
(function(){
    var el = document.querySelector('.od-price-container');
    if(!el) el = document.querySelector('.price-comp');
    return el ? el.innerText.trim().replace(/\s+/g,' ') : 'NO_EL';
})()
```

### Step 4: Parse price text
1688 price format examples:
- `¥ 0 .20 ¥ 10 .81 1个起批 60天老客价` → ¥0.20 (1pc MOQ), ¥10.81 (old-client bulk)
- `券后 ¥ 0 .11 起 3件预估到手单价 ¥ 0 .11 ¥ 12 .39 3个起批` → ¥0.11 (coupon price, 3pc MOQ)
- `新人价 ¥ 0 .24 起 2件预估到手单价 ¥ 0 .74 ¥ 1 .50 2个起批 60天老客价` → ¥0.24 (new user), old-client ¥1.50

### Step 5: Output table
| Link | Shop | Price | MOQ | Notes |
|-------|------|-------|-----|-------|

## Verified price selectors (work on 1688)
```
.od-price-container      ← Yiwu Shengtian / Zhongyuan
.price-comp             ← backup
[class*="price-container"] ← backup
```

## Known issues & fixes
| Issue | Fix |
|-------|-----|
| Spec button inside combo dropdown (Lianheng) | Click combo button first, then sub-spec row |
| Lianheng has no standalone 16×16×16cm button | Open spec dropdown, find matching row |
| Two shops are same-source (Shengtian/Zhongyuan same legal person) | Flag as potential duplicates |
| Only 3 shops have exact 16×16×16cm spec | Inform user: need custom factory or accept close specs |

## File locations
- Precision price script: `~/1688_price_extract.py` (browser_console wrapper)
- Spec price via 1688-cli: `~/1688_spec_price.py` (CLI API, reference only)
- Findchain main: `~/findchain.py`
