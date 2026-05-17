---
name: d-id
description: d-ID用法：照片说话视频、API、Creative Reality Studio
version: 1.0.0
category: creative
---

# d-ID

## When to Use
需要将静态照片转化为说话视频时；历史人物、企业代言、创意内容；需要API批量将图片转视频。

## Core Features
- **照片转视频**：上传照片，AI生成说话/表情动画
- **Creative Reality Studio**：Web界面，无需编码即可创作
- **多语言支持**：配音可选择多种语言和音色
- **API批量生产**：REST API实现自动化视频生成
- **Watermark控制**：付费可去除水印
- **模板预设**：预制开场动画、数字人手势模板

## Quick Start
1. 访问studio.d-id.com，注册登录
2. 点击"Create Video"，上传人物照片
3. 输入配音文本或上传音频，选择语言
4. 生成后下载或嵌入网页
5. API调用：获取API Key后POST到/api/v1/talk

## Pitfalls
- 上传照片需正脸、清晰，否则动画效果差
- 免费版视频有水印且时长受限
- API为异步，生成需等待回调
- 复杂表情动画需高级套餐
