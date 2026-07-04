# 2026-06-21 "所有问题已修复" 验证反例

## 背景
收到"全面验证完成，所有有问题的全部修复"的汇总报告，逐项实测后揭穿：

## 逐项验证结果

| 报告声称 | 实际状态 | 说明 |
|---------|---------|------|
| cua-driver 0.5.7 安装 | ✅ | `cua-driver --version` = 0.5.7, daemon PID 82239 |
| capture(som) | ✅ | Chrome 1488×960, 1974 元素 |
| capture(vision) | ❌ W:0 H:0 | Chrome 前台时 vision 模式拿不到有效截图，未修复 |
| drag/set_value | ⚠️ 参数要求 | 非 bug，是设计行为需要正确参数 |
| scrapping 安装 | ❌ 目录不存在 | `~/.hermes/scripts/scrapping/` 不存在，只有 `~/.hermes/scripts/` 下的 verify_* 脚本 |
| verify_detect.py | ✅ 30项全过 | bot.sannysoft 检测全绿 |
| verify_anti_detect_e2e.py | ✅ 通过 | 截图已保存 /tmp/anti_detect_e2e.png |
| verify_human_click.py | ❌ KeyError | 第163行 `msg["result"]["result"]["value"]` 取不到，CDP event frame 问题 |
| scrapling 0.4.7 | ✅ | StealthyFetcher + Playwright Chromium 都能用 |

## 教训
- "全面验证完成" ≠ 每项都真测了
- "所有有问题的全部修复" 是典型的 aggregate statement，必须拆解
- 目录不存在也是"没修复"的证据，不能假装不存在的东西不存在
- verify_human_click.py 的 KeyError 跟 anti-detection-stealth 里文档的 Chrome 148+ CDP event frame 问题是同一个根因

## 关联
- 已录入 `verification-before-reporting` Failure 30
- CDP event frame 根因见 `browser-automation/anti-detection-stealth` "Chrome 148+ event 帧坑"章节