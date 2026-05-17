# Product Main Image Generation Workflow

## Overview
Generate professional e-commerce product main images optimized for marketplace listings. Produces clean, studio-quality product shots suitable for:
- Amazon product listings
- E-commerce storefronts
- Catalog photography
- Social media product showcases

## Required Models
- SDXL 1.0 Base (`sd_xl_base_1.0.safetensors`)

## Usage

```bash
# Generate main product image
python3 scripts/run_workflow.py \
  --workflow workflows/product_main_image/sdxl_product_main.json \
  --args '{
    "prompt": "professional product photography of minimalist watch on white background, studio lighting, high detail, 8k",
    "negative_prompt": "watermark, text, logo, blurry, low quality, dark background",
    "steps": 30,
    "seed": -1
  }' \
  --output-dir ./outputs/products
```

## Prompt Engineering Tips
- Always specify: `white background`, `studio lighting`, `professional product photography`
- Add: `high detail`, `8k`, `commercial quality` for better results
- Negative prompts: exclude `watermark`, `text`, `logo`, `blurry`, `dark`

## Output Specifications
- Resolution: 1024×1024 (scalable)
- Format: PNG
- Quality: Commercial grade