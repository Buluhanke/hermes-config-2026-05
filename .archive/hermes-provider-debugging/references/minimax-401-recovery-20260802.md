# Case: MiniMax custom provider 401 + openrouter 403 地域封锁 (2026-08-02)

## 现象
Telegram 会话发消息后看到 `⚠️ Provider authentication failed. Check the configured credentials; raw provider details are in the gateway logs.`

## 根因（必须按会话切分）
- 实际 Telegram 会话已切 `tencent/hy3:free` (provider=nous)，日志显示连续 5 次成功调用，无认证错误。
- 报错来自 **QQBot 会话** 仍用 `model=MiniMax-M2.7 provider=custom base_url=http://123.56.67.77:9100/v1`，令牌失效 → `HTTP 401: 无效的令牌`。
- config.yaml 的 `model.default` 仍是 `MiniMax-M2.7`（因为 `/model` 只改当前会话不写默认）。
- 辅助 provider 全用 openrouter → `403: This model is not available in your region`（国内封禁）。

## 关键日志行
```
WARNING agent.conversation_loop: API call failed ... provider=custom base_url=http://123.56.67.77:9100/v1 model=MiniMax-M2.7 summary=HTTP 401: 无效的令牌
WARNING agent.title_generator: Title generation failed: Error code: 403 - {'error': {'message': 'This model is not available in your region.', 'code': 403}}
INFO run_agent: OpenAI client created ... provider=nous base_url=https://inference-api.nousresearch.com/v1 model=tencent/hy3:free
```

## 修复
全部切到 nous/tencent/hy3:free（见 SKILL.md 第 5 步命令），openrouter 残留归零。最后由用户在独立 shell 跑 `hermes gateway restart` 让配置生效。

## 确认配置已生效的核查
```bash
hermes config get model          # default/provider/base_url 应指向 nous
hermes config get auxiliary       # 所有子项 provider=nous
python3 -c "import yaml,json;c=yaml.safe_load(open('/Users/aimac/.hermes/config.yaml'));print('openrouter 残留:',json.dumps(c).count('openrouter'))"  # 期望 0
```

## 教训
- `patch` 改不了 config.yaml → 用 `hermes config set`
- `/model` 不写默认 → 必须改 config.yaml 的 `model.default`
- gateway 不能自重启（SIGTERM 自杀）→ 提示用户在独立 shell 跑
- 诊断先按"会话/平台"切分，再 grep 状态码，别被全局混流误导
