# 人类化路线图：全阶段实现清单

> 验证日期：2026-05-15
> 结论：用户提供的 4 阶段人类化路线图（Ollama本地模型 + Python自动化）在该环境中已 95% 实现，无需重复搭建。

## 各阶段对照

| 路线图阶段 | 对应 Hermes 技能/模块 | 实现程度 |
|-----------|----------------------|---------|
| **Phase 1**: 动作拟真 | `hermes-humanization-core` / `humanization_core.py` | ✅ 完整：human_type, human_move, human_click, human_scroll, 贝塞尔曲线, 错字模拟 |
| **Phase 1**: 验证码 | `ask_vlm()` + `human_move()` 拖滑块 | ✅ VLM解字验证码 + 滑块像素差拖动 |
| **Phase 2**: 视觉感知 | `hermes-vision-agent` / `vision_agent.py` | ✅ vlm_click (截图→VLM→坐标→点击→验证), find_element_by_vision, 微信/1688场景函数 |
| **Phase 3**: 长期记忆 | `hermes-memory-hpc` / `memory_hpc.py` | ✅ JSON方案已实现，ChromaDB包已安装待升级 |
| **Phase 3**: 情绪感知 | `humanization_core.analyze_emotion()` | ✅ Qwen3:8b 本地分析情绪+紧急度 |
| **Phase 4**: TTS | `hermes-voice-module` / `voice_module.py` | ✅ edge-tts (男声云希/女声晓晓), speak, speak_to_file, voice_briefing, voice_alert, emotion_speak |
| **Phase 4**: ASR | `voice_module.py` | ✅ faster-whisper base (cpu/int8), listen, listen_from_mic(需sox) |

## 覆盖的场景函数

完整列表：

- `human_type()` — 打字拟真（1%错字+回退）
- `human_move()` — 贝塞尔曲线+随机控制点+末端减速
- `human_click()` — 移动→悬停0.3-0.9s→按下→抬起
- `human_scroll()` — 分3-5次滚动+随机间隔
- `capture_screen()` — mss极速截屏
- `capture_region()` — 区域截图
- `ask_vlm()` — 本地smolvlm2视觉问答
- `find_element_by_vision()` — 截图→VLM→坐标
- `vlm_click()` — 主流程：截图→找坐标→点击→验证(最多2次重试)
- `analyze_emotion()` — Qwen3:8b情绪+紧急度分析
- `send_message_with_breath()` — 分段发消息+呼吸感间隔
- `human_reading_time()` — 按字数计算阅读时间
- `search_1688()` — 视觉搜索1688商品
- `wechat_send_image()` — 视觉操控微信发图片
- `speak()` — Edge-TTS文字转语音并播放
- `listen()` — Faster-Whisper语音转文字
- `voice_briefing()` — 语音简报
- `voice_alert()` — 紧急告警（女声）
- `emotion_speak()` — 情绪自适应语音

## 未实现的小项

- `capture_region()` 实现有bug（用mon 1而非指定区域）— 低优先级
- `listen_from_mic()` 需要 `brew install sox` — 可选
- ChromaDB 向量升级 — 未来方向
