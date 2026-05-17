# 1688 Product Introduction Comic Guide

Guidelines for creating product showcase comics on 1688 / Alibaba platform.

## Content Type Profile

| Attribute | Value |
|-----------|-------|
| Triggers | 1688产品介绍、产品展示、商品详情、采购指南 |
| Art Style | minimalist (default), manga |
| Tone | neutral (default), warm |
| Layout | four-panel (default), standard |
| Aspect | 4:3 (landscape) for platform compatibility |
| Page Count | 1-6 pages |

## Core Pattern: AIDA for Product Comics

Apply advertising AIDA framework to product comic structure:

| AIDA Stage | Comic Panels | Purpose |
|------------|--------------|---------|
| Attention | Cover splash panel | Hook the buyer with product visual or problem场景 |
| Interest | 2-3 panels showing product in use | Demonstrate features and场景 |
| Desire | Key benefit panel with visual metaphor | Emotional appeal or comparison |
| Action | Final panel with CTA or product info | Clear next step |

## Product Photography Integration

1688产品 comics blend product photography with illustrated characters.

### Integration Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Character+Product | Illustrated character using/showing product | Most common, highest engagement |
| Product Spotlight | Product as "hero" with minimal character context | Simple product features |
| Before/After | Illustrated对比 showing product effect | Cleaning, beauty, tools |
| Cutaway | Character + product cross-section diagram | Technical products |

### Visual Treatment

- Product images: Keep product photos as clean reference within comic panels
- Character style: Simplified manga/minimalist to not compete with product
- Color harmony: Use product brand colors as accent in character outfits
- Visual hierarchy: Product should be visually prominent in at least 3/4 of panels

## Product Comic Storyboard Template

### YAML Front Matter

```yaml
---
title: "[Product Name] - 产品介绍"
product_name: "[Product Name]"
product_category: "[Category: 电子元件/服装/家居/机械/etc.]"
target_buyer: "[Buyer persona: 网店店主/贸易公司/线下批发商]"
key_selling_point: "[Primary USP]"
price_range: "[Price range if relevant]"
moq: "[MOQ if relevant]"
source_language: "[zh/en]"
aspect_ratio: "4:3"
page_count: 4
---
```

### Page Structure

```
## Page 1: Attention Hook
Filename: 01-page-[slug].png
Core Message: Grab attention with recognizable场景 or problem

## Page 2-3: Feature Showcase  
Filename: 0N-page-[slug].png
Core Message: Demonstrate 2-3 key features with visual examples

## Page 4: Product Detail / Specs
Filename: 0N-page-[slug].png
Core Message: Technical details, packaging, certification marks

## Page 5: Value Comparison (optional)
Filename: 0N-page-[slug].png
Core Message: Value proposition vs price / competitors

## Page 6: Call to Action
Filename: 0N-page-[slug].png
Core Message: 收藏店铺/发起询价/查看更多产品
```

## 1688-Specific Visual Elements

Include recognizable 1688 platform elements when appropriate:

| Element | Visual Treatment |
|---------|-----------------|
| 1688 logo/watermark | Small, bottom corner, semi-transparent |
| Product video QR code placeholder | Illustrated phone + QR pattern |
| MOQ badge | Circular stamp style with accent color |
| 诚信通标志 | Shield icon with checkmark |
| 买家保障标签 | Ribbon style badge |
| 工厂/贸易区分 | Badge showing manufacturer vs trader |

## Prompt Template for Product Comics

```
A minimalist product introduction comic page in four-panel grid layout (2×2).
The product [PRODUCT NAME] is featured as the hero element.

Panel 1 - TOP LEFT (Attention): [Scene that resonates with target buyer - problem scenario or aspirational use]
- Character: [Simple illustrated figure in [style]]
- Product: [Product clearly visible, styled as [treatment]]

Panel 2 - TOP RIGHT (Interest): [Product in practical use scenario]
- Show [key feature 1] with visual demonstration
- Character expression: [curious/impressed/atisfied]

Panel 3 - BOTTOM LEFT (Interest cont.): [Second feature or benefit showcase]
- Show [key feature 2] with comparison or demonstration
- Accent color elements: [product brand colors]

Panel 4 - BOTTOM RIGHT (Action): [Product detail + call to action]
- Clean product shot with [MOQ], [price range] if applicable
- Text element: [CTA in Chinese: 立即询价/收藏货源]
- Include subtle [1688 platform element] in corner

Style: Minimalist line art with black outlines, [spot color] accent, clean white background.
Asian business illustration style.
```

## Product Categories & Visual Approaches

| Category | Visual Approach | Accent Colors | Common Scenes |
|----------|----------------|---------------|---------------|
| 电子元件 | Technical cutaway, clean diagrams | Blue, silver | 焊接测试, 电路检测, 包装展示 |
| 服装 | Fashion illustration, fabric detail | Category-specific | 试穿, 面料对比, 批量包装 |
| 家居 | Lifestyle integration,情境展示 | Warm earth tones | 家居布置, 使用演示, 包装尺寸 |
| 机械 | Industrial illustration, safety orange | Industrial colors | 操作演示, 零件拆解, 工厂环境 |
| 美妆 | Before/after, skin tone accuracy | Soft pinks, gold | 试用展示, 成分说明, 包装精致 |
| 食品 | appetizing colors, fresh aesthetic | Warm appetizing colors | 食材展示, 制作过程, 安全认证 |

## Quality Markers

- [ ] Product is visually prominent in at least 3 of 4 panels
- [ ] Target buyer persona is clearly visualized
- [ ] MOQ and price range are mentioned (if relevant to buyer)
- [ ] Clear call-to-action in final panel
- [ ] 1688 platform elements add authenticity
- [ ] Character style complements (doesn't compete with) product
- [ ] Chinese text uses full-width punctuation
- [ ] Spot color used consistently for brand elements