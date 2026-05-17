---
name: 3d-from-photos
description: 从照片生成3D：TripoSR/TripoGA/Gaussian Splatting、Meshy AI
version: 1.0.0
---

# 3D from Photos

## When to Use
需要从单张或多张图片快速重建3D模型时使用。适合电商产品展示、游戏资产草稿、建筑现场记录、虚拟现实内容准备。

## Core Features
- **TripoSR**（Stability AI + MIT）：单张照片→3D网格，2秒生成，品质高，开源可本地部署
- **TripoGA**（Tripo3D Gaussian Splatting）：基于3DGS技术，渲染质量更高，适合渲染管线
- **Meshy AI**：支持图生3D、文字生3D、多视角重建，有免费额度
- **Gaussian Splatting（3DGS）**：隐式表示，无需 mesh，直接渲染高质量新视角
- **Photogrammetry**：传统多图重建，Metashape/Colmap成熟方案
- **Luma AI**：手机拍摄即可生成3D场景，NeRF技术，移动端友好

## Quick Start
### TripoSR（本地）
```bash
pip install gradslam torch
# 使用 huggingface 上的 triposr 模型
python -c "from triposr import *; model = TripoSR(); mesh = model('image.jpg')"
```

### Meshy（在线）
1. 访问 https://meshy.ai 注册
2. 上传图片或输入文字描述
3. 选择风格（写实/卡通），等待1-3分钟
4. 下载OBJ/GLB/FBX格式

### Luma AI
1. 下载 Luma App（iOS/Android）
2. 对物体环绕拍摄10-20秒
3. AI自动重建，可导出NeRF或3D mesh

## Pitfalls
- 单张照片重建质量有限，多角度照片效果更好
- 反射/透明/纯色物体重建难度大
- 高精度3D模型文件体积大
- 商业使用需确认模型许可协议
- 实时渲染需要额外优化（减面、烘焙贴图）
