# 1688 Product Main Image Optimization Workflow

## Overview
Specialized workflow for optimizing product images for 1688, Alibaba, and AliExpress listings. Focuses on:
- Background removal with RMBG/U2Net
- White/neutral background generation
- Aspect ratio standardization (1:1, 3:4, 4:3)
- Resolution optimization (800-2000px)
- Quality enhancement for marketplace standards

## Required Nodes/Models
- `Rembg` (U2Net model for background removal)
- Standard ComfyUI image processing nodes

## Usage

```bash
# Optimize a single product image
python3 scripts/run_workflow.py \
  --workflow workflows/1688_optimization/sdxl_1688_optimize.json \
  --input-image image=./product_photo.jpg \
  --args '{"width": 1024, "height": 1024}' \
  --output-dir ./outputs/1688

# Batch optimize multiple images
python3 scripts/run_batch.py \
  --workflow workflows/1688_optimization/sdxl_1688_optimize.json \
  --input-images image=./photos/*.jpg \
  --args '{"width": 1024, "height": 1024}' \
  --count 10 --parallel 3 \
  --output-dir ./outputs/1688_batch
```

## Platform Requirements
| Platform | Min Resolution | Aspect Ratio | Background |
|----------|----------------|--------------|------------|
| 1688 | 800×800 | 1:1, 3:4 | White |
| Alibaba | 1000×1000 | 1:1 | White/Neutral |
| AliExpress | 800×800 | 1:1, 3:4 | White |

## Recommended Workflows by Use Case
- **Product Main Image**: `product_main_image/sdxl_product_main.json`
- **SKU Variation**: Use `batch_generation/sdxl_batch_product.json` with product-specific prompts
- **Lifestyle/Scene**: Use `batch_generation/sdxl_batch_product.json` with lifestyle prompts