---
name: flux-pro
description: FLUX.1 Pro/Raw/Schnell 三大版本对比与API使用
version: 1.0.0
---

# FLUX.1 图像生成模型系列

## When to Use
- 需要高细节、高逼真度图像
- SDXL级别质量但更快的生成速度
- 商业项目需要明确授权
- Photorealistic（照片级真实）风格需求

## Core Features

**三大版本对比：**

| 版本 | 定位 | 速度 | API价格 | 授权 |
|------|------|------|---------|------|
| **FLUX.1 Pro** | 最强质量 | 慢 | 昂贵 | 商业可授权 |
| **FLUX.1 Raw** | 保留细节 | 中 | 中等 | 个人/商业 |
| **FLUX.1 Schnell** | 极速生成 | 最快 | 便宜 | 开源可商用 |

**FLUX.1 Pro：**
- 最高质量，细节最丰富
- 支持高分辨率输出
- API调用：`model=flux-pro`
- 适合：广告、电影级视觉、复杂场景

**FLUX.1 Raw：**
- 保留原始图像细节，减少AI美化
- 适合：需要真实感的摄影、写实风格
- 在Pro和Schnell之间取得平衡

**FLUX.1 Schnell：**
- 开源模型，可本地部署
- 4步生成，速度极快
- 适合：快速原型、LoRA训练
- 社区生态丰富

**提示词技巧：**
- FLUX对自然语言提示词理解强
- 避免过长过复杂描述
- 写实风格提示词无需过多负面提示
- 推荐包含光照、材质、风格关键词

**分辨率支持：**
- 基础输出：512x512 到 1024x1024
- 部分版本支持更高分辨率
- API端可指定具体尺寸

## Quick Start
```bash
# via API (Replicate/Fal.ai)
curl -X POST https://api.replicate.com/v1/predictions \
  -H "Authorization: Token $REPLICATE_API_TOKEN" \
  -d '{
    "version": "xxx",
    "input": {
      "prompt": "photorealistic portrait of an elderly man, natural lighting",
      "model": "flux-pro"
    }
  }'
```

## Pitfalls
- **Pro价格高**：商业大规模使用成本显著
- **生成速度**：Pro/Raw比Schnell慢很多
- **本地部署**：只有Schnell完全开源可本地运行
- **NSFW限制**：各平台内容政策不同
- **提示词差异**：三个版本对同一提示词响应不同
