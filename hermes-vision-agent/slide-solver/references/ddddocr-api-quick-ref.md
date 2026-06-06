# ddddocr API 真实签名（2026-06-04 实测）

## 三个独立实例，对应三个任务

ddddocr 同一个库，按 `det` / `ocr` 开关可分出三个独立能力，**必须分别实例化**：

```python
import ddddocr

# 1. 滑块拼图缺口识别（det=False, ocr=False）
slide = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
# 调 slide_match(target_img, background_img, simple_target=False)
# 返回 {"target": [x, y]} 字典

# 2. 目标检测（det=True, ocr=False）
det = ddddocr.DdddOcr(det=True, ocr=False, show_ad=False)
# 调 detection(img) → List[List[int]]，每项 [x1, y1, x2, y2, conf, ...]
# 用途：点选验证码、文字+图标混合检测

# 3. 纯 OCR 文字识别（det=False, ocr=True）
ocr = ddddocr.DdddOcr(det=False, ocr=True, show_ad=False)
# 调 classification(img, png_fix=False, probability=False, color_filter_colors=None)
# 默认返回 str，probability=True 时返回 Dict[str, Any]
```

## 关键 API 签名

```python
slide_match(
    target_img: Union[bytes, str, PurePath, PIL.Image.Image],
    background_img: Union[bytes, str, PurePath, PIL.Image.Image],
    simple_target: bool = False
) -> Dict[str, Any]
# 返回值关键字段: result["target"][0] = 缺口 x 偏移（px）

detection(
    img: Union[bytes, str, PurePath, PIL.Image.Image]
) -> List[List[int]]
# 每项 box: [x1, y1, x2, y2, conf, class_id?]

classification(
    img: Union[bytes, str, PurePath, PIL.Image.Image],
    png_fix: bool = False,
    probability: bool = False,
    color_filter_colors: Optional[List[str]] = None,
    color_filter_custom_ranges: Optional[List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]] = None
) -> Union[str, Dict[str, Any]]
```

## 入参接受 4 种类型

- `bytes` — 原始图片二进制
- `str` / `pathlib.PurePath` — 文件路径
- `PIL.Image.Image` — 已加载的图片对象

> Pyright/lint 会把字符串当 Literal 报错，runtime 是对的（鸭子类型）。

## 常见坑

- **必须传滑块小图**：合成测试时只传背景图也能跑出结果（simple_target=True），但真 1688 滑块必须传两张图才准
- **返回类型不一致**：`slide_match` 返 dict，`detection` 返 List[List[int]]，`classification` 返 str 或 dict（看 probability 参数）
- **probability 模式**：classification 加 `probability=True` 返回 `{char: prob, ...}`，不是字符串
- **color_filter**：做颜色过滤的，给点选验证码的"红绿灯识别"用

## 模块加载慢

`DdddOcr()` 第一次实例化会加载 ONNX 模型，~1-2 秒。**模块级单例**，不要在 hot path 里重复 `import ddddocr` 或重复 `DdddOcr()`。
