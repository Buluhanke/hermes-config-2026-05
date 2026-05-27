# .hermes 目录磁盘占用分析（2026-05-26）

## 总量
```
du -sh ~/.hermes/*/
```

| 目录 | 大小 | 说明 |
|------|------|------|
| chrome-debug/ | 4.7G | Chrome 独立 profile，含 On-Device ML 模型 |
| mirofish/ | 915M | 屏幕录制 |
| state-snapshots/ | 1.8G | Hermes 状态快照 |
| hermes-agent/ | 3.5G | Hermes 主程序 |
| sessions/ | 890M | 会话历史 |
| node/ | 191M | Node.js 依赖 |
| skills/ | 215M | 技能库 |
| turix-cua/ | 217M | CUA driver |
| logs/ | 61M | 日志文件 |
| lib/ | 37M | Python 库 |
| include/ | 53M | 头文件 |
| bin/ | 119M | 二进制文件 |
| lsp/ | 99M | LSP 相关 |
| cron/ | 32M | Cron 任务 |
| UI-TARS-desktop/ | 89M | UI-TARS |

**总计约 12.5GB**（不含 chrome-debug 的 4.7G）

## chrome-debug 内部结构（4.7G 无法清理）
```
OptGuideOnDeviceModel/weights.bin         4.0G  ← Chrome ML 模型，删了会重下
OptGuideOnDeviceClassifierModel/weights.bin  120M
optimization_guide_model_store/              152M
Default/Extensions/                          227M  ← Chrome 扩展
Default/Cache/Cache_Data/                     47M  ← 可清理，会重新缓存
Default/Code Cache/                           31M  ← 可清理
```
**结论**：4.7G 中只有约 80M 可清理（Cache/Code Cache），剩余 4.6G 是 Chrome 功能文件。清理意义不大。

## sessions/ 清理记录（2026-05-26）
- 清理 >30 天 sessions：释放约 36MB
- 残留 890MB 为近期活跃 session
- 当前策略：sessions.auto_prune=true（已配置），90天自动清理

## 日志文件清理（2026-05-26）
已清理：
- `tui_gateway_crash.log` 176K
- `web.error.log` 285K
- `web.log`（未显示大小）

当前日志：
- `screen_watcher.log` 38MB（38131行）
- `screen_trigger.log` 32MB（32337行）

如需清理 screen_watcher/trigger 日志：
```bash
# 保留最近 10000 行
tail -10000 ~/.hermes/logs/screen_watcher.log > /tmp/sw_tmp && mv /tmp/sw_tmp ~/.hermes/logs/screen_watcher.log
tail -10000 ~/.hermes/logs/screen_trigger.log > /tmp/st_tmp && mv /tmp/st_tmp ~/.hermes/logs/screen_trigger.log
```