---
name: hermes-vision-route
description: "Use when Hermes 看图片/视觉方案。修复原生视觉路由并实测。"
triggers:
  - 看图片 视觉方案 最优
  - vision_analyze 看不清/走描述路径
  - auxiliary.vision 配置
---

# Hermes 视觉路由最优方案

## 铁律
1. 主模型支持 vision 时必须走原生像素：`agent.image_input_mode: auto` 且 `auxiliary.vision` 不是显式后端（provider=auto 且 model/base_url 为空）。
2. `auxiliary.vision.model` 哪怕只写模型名也算显式覆盖 → 强制 `route: text`，把图交给描述模型；若该模型 403/欠费，看图直接失效。
3. 主模型不换、不绑定模型；只修 aux 备用链，遵守用户「给什么模型就用什么模型」。
4. 修复后必须实测：`scripts/verify_vision_route.py` 输出 `route: native`，再用 `vision_analyze` 读含 19px 小字的图并逐字核对。

## 2026-11 全网结论（数据带日期）
- LMArena Vision 2026-11-19：Claude Fable 5 (High) 1325 #1，OCR 1336、图表 1354。
- Roboflow Vision Evals 2026-11-19：Gemini 4 Neon 91.0%（计数/OCR/推理第一），Carbon 89.4% $0.0061/样本，GPT-6.2 Sol 90.3% $0.0059/样本。
- MMMU-Pro 2026-11-22：GPT-6.2 Astra 89.5 #1；ScreenSpot-Pro：GPT-6 Astra 92.7。
- 文档 OCR：Qianfan-OCR 4B（OmniDocBench v1.5 93.12、OCRBench 880、KIE 87.9）；PaddleOCR-VL-1.6 96.34、TeleOCR 96.91；表格/图表 OCRia-1（表格 91.5、图表 85.1）。
- 小字失效原因：服务先缩图（arXiv 2611.22709）；用 `vision_analyze(region=[x1,y1,x2,y2])` 原图坐标裁剪放大。

## 本机凭据现状（2026-11-26 实测）
- OpenRouter 免费 key：Google/Claude 模型 403 地区限制、Qwen 402；只可试 `nvidia/nemotron-3.5-super-vl:free`。
- Nous Portal：付费模型 404 余额不足；免费 vision 模型 `tencent/hy4-flash:free` 可用（实测 11.7s 全字准确）。
- Gemini 直连 key：gemini-2.5-flash / gemini-3.1-flash-lite 可用；Gemini 4 系列 429 配额不足。
- 百度 OCR `~/.hermes/scripts/baidu_ocr.py`：可读中文但 ×→X、¥→￥，仅作交叉核对，精确符号用 VLM。

## 精度基准（2026-11-26 实测，7 行 40→8px 混合中英数字符号）
- hy4-flash 原生：7.7s，逐字精确 5/7、归一化 7/7、CER 0.0，8px 中文/数字全对；差异仅空格与 ¥/￥。
- Gemini-3.1-flash-lite 备用：6.3s，精确 5/7、归一化 6/7、CER 0.006；8px 把「末」读成「未」；4x 裁切放大后读对。
- 百度 general_basic：2.2s，CER 0.078，¥→￥、×丢失、10px「重量→五量」、8px 数字缺位；accurate_basic 无权限（error 6）。仅做交叉核对。
- 结论：干净图上 8px 是原生视觉可靠下限；小字/压缩图先 `vision_analyze(region=...)` 裁切放大再读。

## OCR 交叉核对（macOS Vision + 百度，恢复原并行方案）
本机仍有 `~/.hermes/scripts/macos_vision_ocr.swift`（Vision 框架，离线）和百度 OCR；`ocr-and-documents` 技能里的 `parallel_ocr.py` 是旧版（顺序调用、按字数+10 评分）。

最优组合：原生 VLM 读语义与精确符号；需要逐字文本时，跑 `scripts/ocr_crosscheck.py <图> --reference <VLM转录>`，两引擎并行、以 VLM 转录为参照选更准者；无参照时回退启发式（Vision +10）。

实测（7 行 40→8px）：原生 VLM CER 0.0；macOS Vision CER 0.043（×→✕、±→土、12px 以下相似字错）；百度 CER 0.078（¥→￥、五量/徵峰、数字缺位）。截图上 Vision 读到正确 PID 33837，百度读成 PD33837。有 VLM 参照时脚本选 Vision（相似度 0.9568 vs 0.9222）。

```bash
python3 ~/.hermes/skills/hermes-vision-route/scripts/ocr_crosscheck.py <图片> --reference <vlm转录.txt>
```

## 修复命令
```bash
hermes config set auxiliary.vision.model ""
hermes config set auxiliary.vision.fallback_chain '["provider: gemini, model: gemini-3.1-flash-lite", "provider: gemini, model: gemini-2.5-flash", "provider: openrouter, model: nvidia/nemotron-3.5-super-vl:free"]'
HERMES_DISABLE_LAZY_INSTALLS=1 ~/.hermes/hermes-agent/.venv/bin/python ~/.hermes/skills/hermes-vision-route/scripts/verify_vision_route.py
```
网关内不能 HUP 自己（守卫拦截）；让用户在外部终端跑 `hermes gateway restart`。

## 验证脚本
见 `scripts/verify_vision_route.py`；输出 `route: native` 才算修好。再用含小字测试图（¥/×/校验码/19px 字）走 `vision_analyze` 逐字核对。
