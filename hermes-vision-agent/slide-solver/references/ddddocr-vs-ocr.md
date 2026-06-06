# ddddocr / OCR / VLM 选型对照

用户问"ddddocr 是不是免费？是不是还是 OCR？"时的标准回答。

## 一句话区分

| 库 | 一句话 |
|---|---|
| **ddddocr** | 深度学习**目标检测/分类**库，识别"图里有什么、坐标在哪" |
| **PaddleOCR / Tesseract** | 传统**OCR**，把图里的**文字**识别成字符串 |
| **VLM (Claude/Gemini/Qwen-VL)** | 通用**视觉理解**，能"看图说人话" |

## 任务对照

| 场景 | 用啥 | 理由 |
|---|---|---|
| 滑块拼图验证码 | **ddddocr** | 找拼图缺口位置，是目标检测 |
| 文字点选验证码 | **ddddocr** (detection + classification) | 找文字坐标 |
| 图标点选验证码 | **ddddocr** (detection) | 找图标坐标 |
| 文档/截图/表格读字 | **PaddleOCR** | 中文高精度，CPU 跑得动 |
| 屏幕 OCR 60ms | **Apple Vision** (macOS 原生) | 快，Hermes 默认桌面 OCR |
| 跨语种通用 OCR | **Tesseract** | 装好就是百搭 |
| 截图理解/UI 问答 | **VLM** (Claude/Gemini) | 唯一能"看图说人话"的 |
| CAPTCHA 验证码 4-6 位数字 | **ddddocr** (classification 模式) | 比传统 OCR 准，免费 |

## 关系图

```
验证码/图块类 ──→ ddddocr (CNN 检测/分类)
                  ↓ 缺图内文字时
                  └──→ 内置 classification (OCR 模式) 或 PaddleOCR

读图内文字  ──→ PaddleOCR / Tesseract / Apple Vision

看图理解  ──→ Claude Vision / Gemini Vision / Qwen-VL (VLM)
```

## ddddocr 的关键优势 vs OCR

- 体积小：~85MB vs PaddleOCR 几 GB
- 速度：CPU 几十 ms
- 免费 + 离线
- 专攻"找坐标"和"找小图"（验证码）
- 缺点：读长文/复杂排版不如专业 OCR

## 选型决策树

```
要处理验证码？
├── 是 → ddddocr
└── 否 → 要读文字？
        ├── 是 → 中文 → PaddleOCR；英文/混排 → Tesseract
        └── 否 → 理解场景内容？
                ├── 是 → VLM (要 API key + 联网)
                └── 否 → 不需要视觉
```
