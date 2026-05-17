# Batch Product Image Generation

## Overview
Generate multiple product image variations in a single workflow:
- Main product shots (3 variations)
- Lifestyle/context shots (2 variations)
- Detail close-ups (2 variations)

Total: 7 images per batch run

## Required Models
- SDXL 1.0 Base (`sd_xl_base_1.0.safetensors`)

## Usage

```bash
# Generate batch with multiple prompt variations
python3 scripts/run_workflow.py \
  --workflow workflows/batch_generation/sdxl_batch_product.json \
  --args '{
    "main_product_prompt": "professional product photography of wireless earbuds on white background, studio lighting",
    "lifestyle_prompt": "young person using wireless earbuds in urban cafe setting, natural lighting",
    "detail_prompt": "close-up macro shot of earbud speaker mesh and silicone tip, detailed product photography",
    "negative_prompt": "watermark, text, logo, blurry, low quality",
    "steps": 30
  }' \
  --output-dir ./outputs/batch

# Automated batch with CSV input
python3 scripts/run_batch.py \
  --workflow workflows/batch_generation/sdxl_batch_product.json \
  --csv products.csv \
  --csv-column prompt \
  --count 20 --parallel 3 \
  --output-dir ./outputs/batch_catalog
```

## CSV Format for Automated Batch
```csv
product_id,main_product_prompt,lifestyle_prompt,detail_prompt
SKU001,product photography of red sneakers on white,person wearing red sneakers running,detail of sneaker sole and laces
SKU002,product photography of leather wallet on wood,wallet on table in coffee shop,close-up of wallet stitching
```

## Parallel Execution
| Tier | Max Parallel Jobs |
|------|-------------------|
| Free/Standard | 1 |
| Creator | 3 |
| Pro | 5 |

Use `--parallel N` to saturate your tier limit.