# 执行-感知反馈循环（Action-Perception Loop）

## 概述

反馈循环是具身智能L4级别的核心组件。在执行操作后，系统需要验证操作是否成功，才能决定下一步行动。没有反馈的Agent只能"盲目操作"，而反馈循环让Agent知道"做对了/做错了/需要重试"。

---

## 为什么需要反馈循环

- **L4执行后，系统不知道操作是否成功** — 执行动作（如点击、输入）只是发出了指令，浏览器或系统是否真正响应需要验证
- **没有反馈的Agent只能"盲目操作"** — 无法区分成功、失败、部分成功三种状态
- **反馈循环让Agent知道"做对了/做错了/需要重试"** — 形成完整的感知-决策-执行-反馈闭环

---

## 三种反馈模式

### 1. 立即验证（Immediate Verification）

执行操作后立即截图，与操作前的截图做diff，检测预期变化是否出现。

**适用场景：** UI状态变化可目视检测（弹窗出现/消失、页面跳转、元素内容变化）

**实现方式：**
```python
import cv2
import numpy as np
from PIL import Image

def screenshot_and_diff(before_img, after_img, expected_region=None):
    """比较两张截图的差异"""
    before = cv2.imread(before_img)
    after = cv2.imread(after_img)
    
    if expected_region:
        x, y, w, h = expected_region
        before = before[y:y+h, x:x+w]
        after = after[y:y+h, x:x+w]
    
    diff = cv2.absdiff(before, after)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    changed_pixels = np.sum(diff_gray > 30)
    
    return changed_pixels > 1000  # 阈值可调
```

**示例：** 点击"提交订单"按钮后，检查是否出现"确认弹窗"

---

### 2. 状态查询（State Query）

执行后查询系统状态，比直接截图更精确、开销更低。

**适用场景：** 文件系统状态、数据库状态、内存状态

**实现方式：**
```python
import os
import time

def verify_file_modified(filepath, timeout=5):
    """检查文件是否在超时时间内被修改"""
    mtime_before = os.path.getmtime(filepath)
    time.sleep(0.5)
    mtime_after = os.path.getmtime(filepath)
    return mtime_after > mtime_before

def verify_element_in_chat(message_text, chat_elements):
    """检查消息是否出现在聊天窗口元素列表中"""
    return any(message_text in elem.get('innerText', '') for elem in chat_elements)
```

**示例：**
- 点击"保存"后，检查文件是否被修改（mtime变化）
- 点击"发送"后，检查消息是否出现在聊天窗口（DOM查询）

---

### 3. 语义验证（Semantic Verification）

用VLM（视觉语言模型）判断操作结果是否符合人类预期的语义含义。

**适用场景：** 复杂UI状态、跨模态验证、需要理解上下文语义

**实现方式：**
```python
def semantic_verify_vlm(screenshot_path, prompt, model="Qwen2.5-VL-7B"):
    """
    使用VLM进行语义验证
    prompt: 验证指令，如"检查询价是否发送成功，界面是否包含发送成功提示"
    """
    # 调用本地VLM推理
    # 返回: {"success": true/false, "reason": "具体判断理由"}
    pass

# 示例
result = semantic_verify_vlm(
    "1688_inquiry_result.png",
    "检查是否出现'询价已发送'或'发送成功'的提示"
)
```

**示例：**
- 检查1688询价是否发送成功（界面是否包含成功提示）
- 检查弹窗内容是否包含价格信息
- 检查错误提示是否与预期相符

---

## 重试策略

```python
def execute_with_retry(action, max_retries=3):
    """
    带重试策略的执行-验证循环
    
    Args:
        action: 可执行的动作对象（包含execute, retry_with_adjustment, try_alternative_method, fail_with_report方法）
        max_retries: 最大重试次数
    
    Returns:
        最终执行结果
    """
    for attempt in range(max_retries):
        result = action.execute()
        
        if verify(result):
            return result
        
        # 回退策略：渐进式调整
        if attempt == 0:
            # 第一次重试：尝试微调参数后重试
            action.retry_with_adjustment()
        elif attempt == 1:
            # 第二次重试：尝试完全不同方法
            action.try_alternative_method()
        else:
            # 所有重试耗尽：记录失败报告
            return action.fail_with_report()
    
    return action.fail_with_report()


def verify(result):
    """验证执行结果是否符合预期"""
    # 根据具体场景实现验证逻辑
    # 返回 True 表示验证通过
    pass
```

---

## 与1688场景的结合

| 操作 | 验证方式 | 预期结果 |
|------|----------|----------|
| 1688询价发送 | 立即验证 + 语义验证 | 出现"发送成功"提示，VLM确认询价单状态 |
| 1688付款 | 状态查询 + 截图验证 | 页面跳转至付款成功页，截图包含"付款成功" |
| 1688投诉提交 | 状态查询 | 获得受理编号，页面显示投诉已提交 |
| 1688商品上架 | 语义验证 | VLM确认商品出现在商品列表页 |

---

## 工具支持

| 工具 | 用途 | 说明 |
|------|------|------|
| **SSIM比较** | 截图相似度检测 | 使用 OpenCV 或 Pillow 的 `ImageChops.difference` |
| **AX树查询** | UI元素状态查询 | 使用 cua-driver 的 `page` 工具查询DOM/AX树 |
| **VLM判断** | 语义级验证 | 使用 Qwen2.5-VL-7B 或等效本地模型进行推理 |
| **Screenshot** | 截图捕获 | 使用 chrome_computer 或 cua_screenshot 工具 |

---

## 集成示例

```python
class ActionPerceptionLoop:
    def __init__(self, action_executor, verification_strategy='auto'):
        self.action_executor = action_executor
        self.verification_strategy = verification_strategy
        self.history = []
    
    def execute_and_verify(self, action, verification_method='immediate'):
        # 1. 执行前记录状态
        screenshot_before = self._capture_screenshot()
        
        # 2. 执行动作
        result = action.execute()
        
        # 3. 根据策略验证
        if verification_method == 'immediate':
            verified = self._immediate_verify(screenshot_before)
        elif verification_method == 'state':
            verified = self._state_verify(result)
        elif verification_method == 'semantic':
            verified = self._semantic_verify(screenshot_before)
        
        # 4. 记录历史
        self.history.append({
            'action': action,
            'result': result,
            'verified': verified
        })
        
        return verified, result
    
    def _immediate_verify(self, screenshot_before):
        screenshot_after = self._capture_screenshot()
        return screenshot_and_diff(screenshot_before, screenshot_after)
    
    def _state_verify(self, result):
        # 实现状态查询验证
        pass
    
    def _semantic_verify(self, screenshot_before):
        screenshot_after = self._capture_screenshot()
        return semantic_verify_vlm(screenshot_after, self.verification_strategy)
```

---

## 最佳实践

1. **优先使用轻量验证** — 状态查询 > 立即验证 > 语义验证，按需升级
2. **保留验证历史** — 用于调试和追溯决策过程
3. **渐进式重试** — 每次重试采用不同策略，避免死循环
4. **明确验证阈值** — 截图diff阈值、VLM置信度等参数需可配置
5. **失败报告结构化** — 记录失败原因、尝试次数、最终状态，供人工复查