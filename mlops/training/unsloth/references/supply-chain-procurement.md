# Supply Chain Procurement Training Context

## User Domain: Packaging Materials Procurement (找品)

### Core Requirements
- **Target suppliers**: Minimum 10 suppliers per search
- **Origin preference**: Jiang-Zhe-Hu (Jiangsu-Zhejiang-Shanghai) region
- **Product categories**: Packaging materials (纸箱, cartons), business supplies
- **Data sources**: 1688, PDD (拼多多), Taobao, YiwuGo
- **Current blockers**: 1688 anti-bot detection, mock data in supply-agent-v11

### Training Goals
- **Supplier matching**: Identify high-quality suppliers from scraped data
- **Price comparison**: Extract and compare prices across platforms
- **Quality assessment**: Evaluate factory certifications, production capacity
- **Procurement workflow**: Automate full procurement pipeline

## Relevant Projects

### `~/supply-agent-v11/`
**Purpose**: Supply chain agent skeleton for finding products

**Structure**:
```
supply-agent-v11/
├── agent.py              # Main agent entry point (currently mock)
├── crawler/              # Platform scrapers (all return empty for now)
│   ├── search_1688.py
│   ├── search_pdd.py
│   ├── search_taobao.py
│   └── search_yiwugo.py
├── engine/               # Ranking engine
│   └── ranker.py
├── extractor/            # Product detail extractor
│   └── detail_page.py
├── matcher/              # Similarity matching
│   ├── similarity.py
│   └── sku_match.py
├── output/               # Result formatter
│   └── formatter.py
└── parser/               # Product parsers
    ├── image_parser.py
    ├── jd_parser.py
    └── spec_parser.py
```

**Status**: All crawler modules return empty lists (mock data)

### `~/1688_bot/`
**Purpose**: 1688 anti-detection and scraping attempts

**Files**:
- `anti_detect_1688.py` — Selenium anti-detection (CDP injection)
- `selenium_1688.py` — Direct Selenium with real Chrome
- `browser_use_scraper.py` — browser-use based scraper
- `cdp_scraper.py` — Direct CDP client
- `cdp_1688.py` — CDP helper script

**Status**: All approaches detected by 1688 anti-bot → return SVG tracker or empty HTML

### `~/dianchacha_v2.5.3/`
**Purpose**: 电查查 (electricity consumption database for supplier verification)

**Status**: Available for quality assessment data

## Data Sources for Training

### Primary (Currently Blocked)
- **1688.com**: Product listings, supplier profiles, prices
  - Status: Anti-bot detection prevents scraping
  - Alternative: Use browser-use with anti-detection techniques (may still fail)

### Secondary (Working)
- **PDD (拼多多)**: E-commerce platform with weaker anti-bot
- **Taobao**: E-commerce platform with moderate anti-bot
- **YiwuGo**: Wholesale market data

### Tertiary (Static)
- **Dianchacha**: Supplier verification via electricity consumption data
- **Manual collection**: User-provided supplier profiles

## Key Metrics for Supplier Evaluation

### Must-Have
1. Origin: Jiang-Zhe-Hu region
2. Minimum 10 suppliers per batch
3. Price competitiveness
4. Product specifications match

### Value-Added
1. Factory certifications (ISO, etc.)
2. Production capacity
3. Logistics speed
4. Quality history

## Training Data Format

### Example Training Pair
```
Input: "找10个江浙沪的纸箱供应商"
Output: [
  {
    "platform": "1688",
    "name": "XX包装材料厂",
    "price": "¥1.2-3.0/个",
    "spec": "30*40*50cm",
    "link": "https://detail.1688.com/offer/123456789.html",
    "quality_score": 0.85,
    "origin": "浙江杭州"
  },
  ...
]
```

## Workflow Integration

### User's Preferred Workflow
1. **Direct execution**: "你给我装" (just install it) — no step-by-step guidance
2. **Short responses**: One-line confirmations like "Done" or "切换完成"
3. **Silent fallback**: If model fails, silently switch without showing technical errors
4. **User corrections override**: Stop and use corrected method immediately

### Agent Behavior
- **NO**: "Let me explain how this works..." or "Here are the steps..."
- **YES**: "切换完成" (Switched) or "Done"
- **NO**: "The API call failed, switching to fallback..."
- **YES**: Silent fallback with result

## Next Steps

1. **Data collection**: Scrape PDD/Taobao to build training dataset
2. **Model fine-tuning**: Train on supplier matching and price comparison tasks
3. **Evaluation**: Test on real procurement queries
4. **Integration**: Connect trained model to supply-agent-v11
