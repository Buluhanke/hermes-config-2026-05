# OCR + VLM 混合坐标提取方案

**日期**: 2026-06-06
**来源**: 方向 D 深度分析 + 实际代码改造
**适用场景**: 需要屏幕元素坐标但 VLM 不支持 bbox 输出的情况

## 问题

qwen3-vl:2b（及多数轻量 VL 模型）**不支持直接输出 bbox 坐标**。测试验证：
- 纯文本问答：✅ 正常
- 带图元素识别：✅ 正常（返回元素名称列表）
- 带图 bbox 输出 prompt：❌ 返回空或截断
- 带图文字坐标描述：❌ 返回"没看到截图"

## 解决方案：OCR + VLM 混合

```python
def get_scene_type(image_path):
    """
    返回: {
        "scene": "browser|desktop|unknown|...",
        "elements": [{"text": "...", "x": 0, "y": 0, "w": 0, "h": 0}, ...],
        "element_count": N
    }
    """
    # 1. OCR 获取文字 + bbox
    rects = ocr_get_text_with_rects(image_path)
    
    # 2. VLM 做场景分类（用 OCR 文本做上下文提升准确率）
    ocr_texts = [r['text'] for r in unique_rects[:20]]
    scene = classify_scene(image_path, ocr_texts)
    
    # 3. 合并输出
    return {"scene": scene, "elements": unique_rects, "element_count": len(unique_rects)}
```

## 为什么可行

1. **百度 OCR 原生支持 bbox**：返回每个文字块的 left/top/width/height
2. **VLM 擅长分类而非定位**：qwen3-vl:2b 做场景分类准确率远高于定位
3. **两者互补**：OCR 提供"有什么+在哪"，VLM 提供"这是什么场景"
4. **OCR 失败时回退**：ocr_get_text_with_rects 返回空时，自动退化为纯 VLM 场景分类（原逻辑）

## 代码实现

handler.py 已实现：
- `load_ocr_config()` — 从 RPA 脚本加载百度 API 密钥
- `ocr_get_text_with_rects(image_path)` — 调用百度 OCR，过滤重复和太短文本
- `get_scene_type_v1(image_path)` — 原 VLM 分类逻辑（重命名为 v1）
- `get_scene_type(image_path)` — v2 混合方案，自动 OCR + VLM 合并
- `auto_execute(scene_type, answer, elements=None)` — 接收 elements 参数

## 已知限制

1. OCR 对非文字元素无效（图标、按钮图形、图片广告）
2. 百度 OCR 免费额度 1000次/天
3. OCR 精度受截图分辨率影响（建议 1920x1080+）
4. 中文识别精度 > 英文，非标准字体识别可能失败
5. 坐标是截图坐标系，实际点击需要转换为 screen/window 坐标系

## 后续改进方向

1. 考虑引入专门 GUI grounding 模型（如 UI-Venus 1.5、Mano-P）作为 OCR 补充
2. 屏幕分辨率自适应（检测 DPI 自动调整 OCR 参数）
3. 多窗口场景：需要窗口级坐标转换（当前返回的是全局屏幕坐标）
