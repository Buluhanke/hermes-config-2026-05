# 磁盘健康参考（2026-06-02 实测）

## Mac mini M4 24GB 典型磁盘布局

| 目录 | 典型大小 | 说明 |
|------|---------|------|
| `~/.hermes` | ~11G | 日志、截图、memory、skills、references |
| `~/Library/Application Support` | ~17G | macOS 应用数据（含 Chrome、Ollama、Hermes等） |
| `~/Library/Caches` | ~10G | 系统/应用缓存 |
| `~/Downloads` | ~3G | 下载文件 |
| `~/Desktop` | ~54M | 桌面文件 |
| `~/Brain_Lab` | ~196K | 用户知识库（极小） |

**合计**：约38G（2026-06-02 实测值，随时间增长）

## 高增长风险目录

- `~/.hermes/logs/` — 每日进化日志+screen_trigger日志，持续增长
- `~/.hermes/screenshots/` — 截图积累，每张~2-5MB
- `~/.hermes/memory/` — 学习日志文件，可数百KB
- `~/.hermes/skills/` — reference文件积累，增长缓慢
- `~/Library/Caches` — 浏览器缓存，需定期清理

## 已知大文件（历史遗留）

- `~/.hermes/autonomous-ai-agents/` — 曾有RPA相关代码，已清理
- Ollama模型文件：qwen3-vl:2b (1.76GB) + qwen2.5:1.5b (0.99GB) 存在 `~/.ollama/models/` 下

## 清理推荐

### 每日进化自动清理
```bash
# 日志轮替（15天以上）
find ~/.hermes/logs -name "*.log" -mtime +15 -delete
# 旧截图（7天以上） 
find ~/.hermes/screenshots -name "*.png" -mtime +7 -delete 2>/dev/null
```

### 手动大清理（需用户批准）
```bash
# 查看最大的目录
du -sh ~/.hermes/*/ 2>/dev/null | sort -rh | head -10
# 清理所有截图（如无保留价值）
rm -rf ~/.hermes/screenshots/*.png
# 清理全部日志（如无保留需要）
rm -rf ~/.hermes/logs/*.log
```
