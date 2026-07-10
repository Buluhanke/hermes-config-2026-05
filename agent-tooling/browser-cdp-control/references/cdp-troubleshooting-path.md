# CDP 故障排查路标（2026-07-10 新增）

## 第一定律：先查 Gateway，再查工具本身

当 browser/CDP/CLI 工具报莫名其妙的错（Connection refused、404、"没授权"），**第一件事**：

```bash
pgrep -f "hermes-gateway" | wc -l   # 0 = Gateway 停了
ps aux | grep hermes-gateway | grep -v grep
```

Gateway 是所有工具的枢纽。OmniRoute 报 500、browser_navigate 失败、工具全报错 — 先确认 Gateway 活着。

**重启 Gateway**：
```bash
bash ~/.hermes/scripts/restart_gateway.sh
```

## 第二定律：CDP 端口看 4 个地方

browser 工具报错但 `curl localhost:9222/json/version` 成功 → CDP 端口配置漂移。

**4 个地方全扫**：
```bash
echo $BROWSER_CDP_URL
grep -n "BROWSER_CDP_URL\|cdp_url" ~/.bash_profile ~/.zshrc 2>/dev/null
grep -n "cdp_url\|browser" ~/.hermes/config.yaml
grep -n "BROWSER_CDP_URL\|cdp_url" ~/.hermes/.env
```
优先级：env > config > auto。4 个地方全一致才算对。

## 第三定律：hermes_cdp_bot.py 每次用前查 tab ID

脚本里有硬编码 DeepSeek tab ID，Chrome 重启后必变。**每次运行前**先：
```bash
python3 ~/.hermes/scripts/hermes_tab_switch.py list
```
tab_id 不一致则更新脚本里的 `DEEPSEEK_TAB`。

## 第四定律：Python 3.14 asyncio.run 变了

```python
# ❌ Python 3.14 报错
asyncio.run(main())

# ✅ 兼容所有版本
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(main())
finally:
    loop.close()
```

## 第五定律：OmniRoute 500 不是总代表坏了

Server 进程在 + curl 能连 = 问题在 DB 初始化或 better-sqlite3 ABI，不在连接。
