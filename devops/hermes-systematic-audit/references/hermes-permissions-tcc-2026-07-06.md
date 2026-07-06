# Hermes 本机掌控权限参考（2026-07-06 整理）

## 用户身份
- 标准管理员用户（uid=501 staff），**非 root**
- `sudo -n` 需要密码，**无法无密码 sudo**

## TCC 权限现状

### ✅ 已有
| 权限 | TCC Service 名 | 持有者 |
|---|---|---|
| Apple Events（自动化控制） | `kTCCServiceAppleEvents` | `com.trycua.driver`（cua-driver 0.6.8）✅ |
| Apple Events | `kTCCServiceAppleEvents` | `com.apple.Terminal` |
| 屏幕录制（Ax Tree） | `kTCCServiceScreenCapture` | Chrome（多个 profile） |

### ❌ 缺失
| 权限 | 影响 |
|---|---|
| Screen Recording（TCC 层） | 无法用 AX API 读屏（但 cua-driver 有 Apple Events 权限，不依赖此条）|
| Full Disk Access | 无法读 `/Library/Mail` 等系统目录 |

## Hermes 实际掌控链路
```
用户 → Telegram/QQ/微信 → Hermes Gateway (PID 13339)
                          │
                          ├─ cua-driver ──→ 屏幕/窗口/鼠标/键盘 (Apple Events TCC ✅)
                          ├─ Chrome CDP :9222 ──→ 浏览器 DOM/Network/Console
                          ├─ browser-use daemon ──→ 远程浏览器自动化
                          ├─ 终端(Python/Bash) ──→ 文件/网络/系统
                          └─ 18个 LaunchAgents ──→ 定时任务/守护进程
```

## LaunchAgents 运行状态（2026-07-06）
```
PID 13339  ai.hermes.gateway      ← Gateway 主进程
PID 1129   ai.hermes.webhook      ← Webhook 服务
-78        ai.hermes.dashboard
-0         ai.hermes.idle-browser-killer
-0         ai.hermes.chrome-keepalive
-0         ai.hermes.daily-health
-0         ai.hermes.self-evolution
-0         ai.hermes.self-check
```
注意：大部分 LaunchAgents 是 `0`（未激活），gateway 靠直接启动而非 launchd 管理。

## DB 活跃度时间戳模式（已验证）
```
perception_memory.element_cache.last_hit_at    → Unix timestamp（1782703386 = Mon Jun 29 11:23:06 2026）
verification_evidence.verification_events.created_at → ISO string
response_store.responses.accessed_at          → Unix timestamp（NULL = 从未访问）
state.db messages.timestamp                   → REAL Unix timestamp
```

## 判断 DB 活跃度的标准三连
```bash
sqlite3 <db_path> ".tables"
sqlite3 <db_path> ".schema" | head -60
python3 -c "
import sqlite3, time
conn = sqlite3.connect('<db_path>')
# 找时间戳列并查 MAX
cur = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
for t in cur.fetchall():
    try:
        r = conn.execute(f'SELECT MAX({t[0]}_at) FROM {t[0]}').fetchone()[0]
        if r: print(f'{t[0]}: {time.ctime(r)}')
    except: pass
"
```
