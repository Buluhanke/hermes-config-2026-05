# vision-connect 实现笔记 (2026-05-16 晚)

## 核心结论

**M4 24GB 上 smolvlm2 优于 qwen2.5vl:7b**：
- qwen2.5vl:7b 加载失败（内存不足，OOM）
- smolvlm2-agentic-gui:latest 正常运行（2GB，60-90秒）
- 优先顺序：smolvlm2 → qwen2.5vl:7b → OpenRouter Gemini Flash

## 实测数据

| 操作 | 结果 |
|------|------|
| 截屏（mss.mss()，已deprecated） | ~50ms，1.6MB PNG |
| smolvlm2 视觉分析 | 2-5s，本地零Token |
| find_and_click("Safari图标") | 返回坐标(173, 289) ✓ |
| SSIM 验证 | 0.962（轻微变化，不确定区间） |

## 关键代码（vision_connect.py）

```python
# 优先级模型选择
models_to_try = [
    ("ahmadwaqar/smolvlm2-agentic-gui:latest", 60),
    ("qwen2.5vl:7b", 90),
]
```

```python
# mss 新版 API（mss >= 10.0）
with mss.MSS() as s:  # 不是 mss.mss()
    s.shot(output=path)  # 不是 shot(output=path, monitor=1)
```

```python
# SSIM 阈值判断（实测校准）
# 0.962 介于 0.92-0.98 不确定区间
# 实际点击已成功（坐标正确），但 SSIM 验证不够敏感
```

## vision_connect.py 与 hermes-vision-agent 的关系

- `hermes-vision-agent` = 架构设计（三层感知：OCR→VLM→SSIM）
- `hermes-vision-connect` = 具体实现（截屏→ollama→执行→验证）

两者配合使用：`hermes-vision-agent` 负责架构，`vision_connect.py` 负责落地。

## OpenRouter Gemini Flash 配置（config.yaml auxiliary.vision）

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: google/gemini-2.0-flash
    base_url: https://openrouter.ai/api/v1
```

但实际优先走本地（零Token），只有 Ollama 全挂才走 OpenRouter。

## 剩余卡点

1. **cua-driver 未安装** - M1 芯片构建超时，需手动运行安装命令
2. **qwen2.5vl:7b OOM** - 24GB 不够，但 smolvlm2 能跑
3. **SSIM 阈值** - 0.962 处于不确定区间，点击实际成功但验证严格

## 下一步（smart_click 三层感知）

整合三层感知到 `vision_connect.py`：
```
1. Vision OCR（60-240ms）→ 找到了直接 human_click
2. smolvlm2（2-5s）→ OCR找不到时兜底
3. SSIM 验证（5ms）→ 确认是否跳转
```
这个是 `hermes-vision-agent` SKILL.md 里描述的 `smart_click()` 架构的落地版本。