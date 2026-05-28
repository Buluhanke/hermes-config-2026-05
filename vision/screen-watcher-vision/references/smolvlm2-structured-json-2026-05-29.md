# smolvlm2 结构化 JSON 输出测试（2026-05-29）

**来源**：idle_learning 方向D cron 任务
**模型**：`ahmadwaqar/smolvlm2-agentic-gui:latest`（Q4_K_M, 1.85GB）
**目的**：验证 smolvlm2 能否输出结构化 JSON 用于 auto-execute 精确动作规划

## 测试结果

### 测试1：场景分类（标准 prompt）
```python
prompt = "[这是macOS系统截图，不是照片]\n看这张截图，判断这是什么场景？\n选项：浏览器/微信/桌面/计算器/京东/1688/钉钉/Telegram/其他\n只回答选项之一。不要其他文字。"
```
- **响应时间**：12.9s
- **输出**：`设置\n<code>\nset\n</code>`
- **清理后**：`设置`
- ✅ `get_scene_type()` 的 `<code>` 标签清理逻辑正常工作

### 测试2：结构化 JSON（新 prompt）
```python
prompt = "[这是真实截图，不是风景照]\n用JSON格式回答：\n{\"scene\": \"当前场景类型\", \"elements\": [\"列表UI元素\"], \"has_interactive\": true/false}\n只输出JSON，不要其他文字。"
```
- **响应时间**：1.9s（异常快，可能是缓存）
- **输出**：`3D Model\n<code>\n{\n  "type": "3D Model",\n  "elements": [{"name": "3D Model", "description": ""}]\n}\n</code>`
- **清理后**：包含有效 JSON（但内容是幻觉）
- ⚠️ 1.9s 响应太短（可能缓存），未验证带真实截图的可靠输出

## 关键发现

1. **`<code>` 标签始终包裹输出**：场景分类和 JSON prompt 的输出都包含 `<code>...</code>` 包装
2. **`get_scene_type()` 已有清理逻辑**：`response.split('</think>')[-1].strip()` + `.split('<code>')[-1].strip()` + `.rstrip('</code>').rstrip(')').strip()`
3. **JSON 输出需增强清理**：除 `<code>` 标签外，还需处理头部无效文字（如"3D Model\n<code>\n"）
4. **JSON 可靠性待验证**：short response 可能是缓存，需重复测试确认

## 清理函数改进建议

```python
def clean_smolvlm_response(raw: str) -> str:
    """清理 smolvlm2 输出，去除 think/code 标签"""
    cleaned = raw
    # 1. 去除 think 标签
    cleaned = cleaned.split('</think>')[-1]
    # 2. 提取 <code>...</code> 内部内容（如果有）
    if '<code>' in cleaned and '</code>' in cleaned:
        start = cleaned.find('<code>') + 6
        end = cleaned.find('</code>')
        cleaned = cleaned[start:end].strip()
    # 3. 清理其他包装字符
    cleaned = cleaned.rstrip(')').strip()
    return cleaned
```

## 结论

- smolvlm2 **可以**输出结构化 JSON，但总是带 `<code>` 标签包装
- 对于 auto-execute，JSON 输出的可靠性需更多测试验证
- 现有场景分类 pipeline（字符串匹配）足够稳定，不需要立即迁移到 JSON
- 当有更强模型（如 InternVL3-1B）时，JSON 输出 + auto-execute 组合会更可靠
