# 看图题视觉方案调研与复盘（2026-11-23）

## 事故复盘
第一次考试在第19题(纯图标题)现场试视觉模型：vision 主模型无额度 → OpenRouter 免费模型 llama 下架/gemma 限流 → PIL 像素聚类，耗几分钟超过 44 秒/题限时，考试失败。补考改用预读+像素秒判，19/20 通过。根因：**考试热路径上找工具**，而非开考前确认通道。

## 方案对比（实测 2026-11-23）

| 方案 | 可行性 | 速度 | 依赖 | 结论 |
|---|---|---|---|---|
| `nvidia/nemotron-3.5-super-vl:free` + OpenRouter key | ✅首测成功(识别出图标)，但国内网络 HTTP=000 连续超时 | 4.9s(通) | 现有 OPENROUTER_API_KEY | **首选**，加多模型fallback+重试 |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 同上，reasoning 吃 token | 6s | 同上 | fallback #2 |
| `google/gemma-4-31b-it:free` | 429 限流 | - | 同上 | 不稳定，fallback #3 |
| `openrouter/free` 路由 | 自动选可用免费视觉模型 | 不定 | 同上 | 兜底路由 |
| shujuyu.cn 学法减分题库 API | ✅API完整(query/search/含图题images)，需注册 key | ~0.3s | 注册+¥0.002/次 | **开考前注册最稳**（直接按题干拿答案） |
| 百度 OCR + PIL 像素法 | ✅已在补考验证19/20 | <2s | 无 | 兜底，主题色需极纯色阈值 |
| GLM-4V-Flash(智谱) | 免费视觉，需注册 | - | ZAI key | 备选 |
| LLM7.io 匿名视觉 API | 免注册 OpenAI 兼容，60次/时 | - | 无 | 备选，海外延迟待测 |

## 关键坑（已修复进 xfjf_vision.py）
1. **reasoning 模型 max_tokens 必须 ≥600**：给 300 时 content=None，全被 reasoning 吃光（实测 q19 首调返回 content=None、reasoning 里才有分析）。
2. **禁用 reasoning 的 `reasoning:{"enabled":false}` 参数会让请求空返回**，别用；给足 max_tokens 即可。
3. **App 主题绿像素 16 万级**会污染灯色判定：必须用极纯色阈值(R>200,G<70,B<70)+面积<3000 的孤立灯块，否则整屏绿误判为绿灯。q9 用极纯色正确判红灯448像素。
4. 免费模型会下架(llama vision)、限流(gemma 429)、国内网络超时(HTTP=000)，**必须4模型fallback+2次重试**，且失败不阻塞(像素兜底)。

## 迭代后工作流（下次直接用）
- 开考前：`xfjf_vision.py` 对一张测试图跑通视觉通道；有 shujuyu key 则直接用题库 API 预取全部答案。
- 考试中：看图题 `screencap` → `xfjf_vision.py <图> <题干>` → 返回字母+来源，1-10秒。视觉全失败时像素法兜底，判不出返回 null 才由模型/用户定。
- 脚本位置：`scripts/xfjf_vision.py`（视觉优先+像素兜底，零硬编码坐标）。
