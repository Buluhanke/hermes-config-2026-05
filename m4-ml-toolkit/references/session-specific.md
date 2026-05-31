# 2026-05-31 会话：模型提供商切换 + M4 ML 工具箱搭建

## 背景

v2.aicodee.com (MiniMax-M2.7-highspeed) 额度不足(403)，minimax-cn 备用超限(429)。

## 模型连通性测试

Python 脚本统一测试，避免 shell 变量脱敏问题。

结果:
1. ❌ v2.aicodee.com → 403 额度不足
2. ❌ minimax-cn → 429 超限
3. ✅ DeepSeek 直连 → OK (0.7s)
4. ✅ OpenRouter / deepseek/deepseek-v4-flash → OK

## 配置更改

改前: MiniMax-M2.7-highspeed / custom (v2.aicodee.com)
改后: deepseek/deepseek-v4-flash / openrouter

## Nous Portal 历史 (2026-05-21)

用户曾配置 Nous Portal (billing="nous") + deepseek/deepseek-v4-flash。
后续配置变更覆盖了 OAuth 令牌。恢复需 `hermes setup --portal`。

## M4 ML 环境

已装: torch 2.12, torchvision 0.27, transformers 5.9, Pillow, scikit-image 0.26, ultralytics 8.4, rembg 2.0

### 性能
- ViT 分类: 2.9s (google/vit-base)
- YOLOv8n: 170ms ✅
- rembg: 首次16s, 后续2.2s

### 教训
qwen3-vl:2b 占用 16.7GB RAM — 是系统卡顿主因。已用 YOLO+rembg+PaddleOCR 替代。
