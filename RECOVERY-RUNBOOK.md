# Hermes 灾难恢复手册（RUNBOOK）

> **用途**：本机故障/换电脑时，照本手册逐步恢复 Hermes 全部能力。
> **维护**：2026-11-23，基于本机实测配置（macOS 27.0.1 / arm64 / Hermes v0.23.2 stable）。
> **重要**：本手册**不含任何密钥**。密钥需单独从原机 `.env` 迁移或重新申请（见 §6）。

---

## 目录（菜单）

| 步骤 | 内容 | 恢复后得到什么 |
|---|---|---|
| §1 | 安装 Hermes 本体 | 可运行的 hermes 命令 + gateway |
| §2 | 恢复技能（skills） | 272 个技能 + 87 个外部技能 |
| §3 | 恢复配置（config.yaml） | provider / MCP / 平台接线 |
| §4 | 恢复记忆 | 439 条事实 + 用户偏好 |
| §5 | 恢复定时任务（cron） | 12 个定时任务 |
| §6 | 恢复密钥（.env） | 116 个 API key（**敏感，手动迁移**）|
| §7 | 恢复外部工具与设备 | scrcpy / adb / 两台设备 / 路由器 |
| §8 | 恢复脚本与桌面插件 | 263 个脚本 |
| §9 | 验证清单 | 逐项确认恢复成功 |

---

## §1 安装 Hermes 本体

```bash
# 本机是 git clone 安装，版本 v0.23.2 stable (ae2a81c)
# 官方文档为准：https://hermes-agent.nousresearch.com/docs
# 安装后确认：
hermes --version        # 应显示 v0.23.2 或更新
which hermes            # 本机: /Users/aimac/.local/bin/hermes
```

**Gateway（后台服务）**：本机由 launchd 托管
- 标签：`ai.hermes.gateway`（另有 `ai.hermes.cleanup-logs`）
- 健康检查：`curl -s http://127.0.0.1:18789/health`
- 重启：`launchctl kickstart -k gui/501/ai.hermes.gateway`
- ⚠️ 用户铁律：不绑定模型、不自动切模型。换机后 config 里的模型设置按 §3 恢复。

---

## §2 恢复技能（GitHub 已备份 ✅）

```bash
# 主仓库（272 个技能 + 全部技能脚本）
git clone https://github.com/Buluhanke/hermes-config-2026-05.git ~/.hermes/skills

# 若已有仓库，只需拉取：
cd ~/.hermes/skills && git pull origin master
```

**外部技能仓库**（87 个技能，5 个独立 clone，内容不在主仓库）：
按 `~/.hermes/skills/EXTERNAL-SKILL-REPOS.md` 的清单逐个 clone，例如：

```bash
cd ~/.hermes/skills
git clone https://github.com/anthropics/skills.git anthropics-skills
git clone https://github.com/mattpocock/skills.git mattpocock-skills
git clone https://github.com/obra/superpowers.git superpowers
git clone https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git ui-ux-pro-max
git clone https://github.com/Graphify-Labs/graphify.git Graphify-Labs-graphify
# 每个仓库切到清单里的精确 commit（记录在该 md 里）
```

**自动备份脚本**：`~/.hermes/scripts/hermes-git-backup.sh`（从 `.env` 读 token，每天定时推 GitHub）

---

## §3 恢复配置（config.yaml）⚠️ 未备份，需手动重建

本机 `~/.hermes/config.yaml`（12KB）**不在 GitHub 上**。恢复方式二选一：

- **A. 从旧机拷贝**：`scp <旧机>:/Users/aimac/.hermes/config.yaml ~/.hermes/config.yaml`
- **B. 按下面清单重建**（关键项）：

```yaml
model:
  provider: nous
  # base_url: https://inference-api.nousresearch.com/v1

providers:
  # 已配置：nvidia / google / zhipu / openrouter / dashscope(qwen) / groq / huggingface
  # 每个 provider 的 base_url 见下方对照；api key 从 .env 引用
```

**Provider base_url 对照**（实测）：
| Provider | base_url |
|---|---|
| NVIDIA NIM | https://integrate.api.nvidia.com/v1 |
| Google Gemini | https://generativelanguage.googleapis.com/v1beta |
| 智谱 GLM | https://open.bigmodel.cn/api/paas/v4 |
| OpenRouter | https://openrouter.ai/api/v1 |
| 阿里 DashScope | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| Groq | https://api.groq.com/openai/v1 |
| HuggingFace | https://api-inference.huggingface.co/v1 |

**MCP 服务器**（config.yaml 的 `mcp_servers:` 段）：
- `filesystem` — mcp-server-filesystem，args: `/`
- `github` — mcp-server-github
- `memory` — mcp-server-memory
- `taibu` — streamable_http，https://mcp.mingai.fun/mcp
- `openclaw` — command: openclaw, args: mcp
- `fluxdown` — 端口 17801（token 在旧机，需重新申请）

**平台接线**：telegram / feishu / qqbot / wecom / weixin（凭据在 .env，见 §6）

---

## §4 恢复记忆 ⚠️ 未备份，需从旧机拷贝

| 文件 | 内容 | 恢复命令 |
|---|---|---|
| `~/.hermes/memory_store.db` | 439 条事实（4.4MB） | `scp <旧机>:~/.hermes/memory_store.db ~/.hermes/` |
| `~/.hermes/MEMORY.md` | 全局记忆（1.6KB） | 同上 |
| `~/.hermes/USER.md` | 用户画像/铁律 | 同上（若存在） |
| `~/.hermes/SOUL.md` / `HERMES.md` | 人格设定 | 同上 |
| `~/.hermes/memories/` | profile 记忆目录 | `scp -r <旧机>:~/.hermes/memories ~/.hermes/` |

⚠️ `memory_store.db` 用 WAL 模式，拷贝时**连同 `-wal` / `-shm` 一起**，或先停 gateway 再拷。

---

## §5 恢复定时任务（cron）⚠️ 未备份，需从旧机拷贝或重建

本机 `~/.hermes/cron/jobs.json` 含 12 个任务：

| 任务 | 周期 | 作用 |
|---|---|---|
| hermes-desktop-watchdog | 每 3 分 | 桌面守护 |
| self-heal-watchdog | 每 10 分 | 自愈守护 |
| ai-patrol | 每天 9:00 | AI 巡逻 |
| night-learning | 每天 3:00 | 夜间学习 |
| morning-briefing | 每天 8:00 | 早报 |
| monthly-finance | 每月 1 日 9:00 | 月度财务 |
| 每日全网自学 | 每天 3:00 | 自学 |
| 夜间自我进化 / 每晚自我进化 | 22:00 / 23:00 | 进化循环 |
| public-apis sync | 每周一 4:00 | API 同步 |
| WebMCP进展追踪 | 每周一 10:00 | WebMCP 追踪 |
| fact-gate-weekly | 每周日 4:00 | 事实审计 |

恢复：
```bash
# 方式A：直接拷贝 jobs.json
scp <旧机>:~/.hermes/cron/jobs.json ~/.hermes/cron/
# 方式B：用 hermes cron 交互重建（见 hermes cron --help）
hermes cron list     # 验证
```

⚠️ **cron 可靠性坑**（实战）：
- agent 模式 cron 的 script 字段留空或真调 skill，放 echo 占位会架空任务
- bash 内嵌 python 变量必须带 `$`，漏写会 NameError → set -e 挂死
- macOS 无 `timeout` 命令
- gateway 改 env 后需 `launchctl kickstart -k gui/501/ai.hermes.gateway` 重载

---

## §6 恢复密钥（.env）⚠️ 敏感，绝不传公开 GitHub

本机 `.env` 有 **116 个** key，分类恢复：

| 类别 | 关键项 | 获取方式 |
|---|---|---|
| LLM | OPENROUTER_API_KEY / GEMINI_API_KEY / DEEPSEEK_API_KEY / ZAI_API_KEY / NVIDIA NIM | 各厂商控制台 |
| GitHub | GITHUB_MCP_TOKEN / GITHUB_PERSONAL_ACCESS_TOKEN | GitHub Settings → Tokens |
| 搜索 | FIRECRAWL_API_KEY / SERPER_API_KEY / BAIDU_* | 各厂商控制台 |
| 平台 | FEISHU_APP_ID/SECRET / TELEGRAM_BOT_TOKEN | 各平台 Bot 后台 |
| OCR | BAIDU_API_KEY / BAIDU_SECRET_KEY | 百度智能云 |

恢复方式：
- **推荐**：旧机 `.env` 用 1Password / 加密 U 盘迁移到新机 `~/.hermes/.env`，权限 `chmod 600`
- **备选**：重新申请关键项（先恢复 OpenRouter + GitHub + 主模型 3 个即可跑起来）

⚠️ 用户铁律：不绑定任何模型。模型失效时手动切换，不用自动轮替守护。

---

## §7 恢复外部工具与设备

### scrcpy / adb
```bash
brew install scrcpy
adb 路径：~/.local/bin/adb（符号链接到 ~/adb-tools/platform-tools/adb）
```

### 设备清单（实测 2026-11-23）
| 设备 | 地址 | 备注 |
|---|---|---|
| 小米 MI8 | 192.168.8.204:5555 / USB d0b859af | 锁屏 PIN 0000；root/Magisk |
| 华为平板 MRX-W29 | 192.168.8.248:5555 | Android 12；输入法 ADBKeyboard |
| GL-BE6500 路由器 | 192.168.8.1 | root SSH 免密（脚本 ~/.hermes/scripts/router-ssh-enable.sh）|
| Mac Pro | 192.168.8.123 / .156 | user=mac，SSH 免密（别名 macpro / macpro-alt）|

### 设备控制脚本（需从旧机拷贝，不在 GitHub）
| 脚本 | 位置 | 作用 |
|---|---|---|
| `scrcpy-phone` | `~/scrcpy-phone` | 统一入口，选1=MI8 选2=平板，自动重连+uhid 键盘 |
| `pad-type` | `~/pad-type` | 平板文字输入（ADBKeyboard B64 广播，中英文通吃）|

⚠️ 华为平板输入法：默认是 ADBKeyboard（`com.android.adbkeyboard/.AdbIME`）用于电脑输入；用户手打时需切回百度/小艺输入法。

---

## §8 恢复脚本与桌面插件 ⚠️ 未备份，需从旧机拷贝

```bash
# 263 个脚本
scp -r <旧机>:~/.hermes/scripts ~/.hermes/
# 桌面插件
scp -r <旧机>:~/.hermes/desktop-plugins ~/.hermes/
# 关键脚本示例
hermes-git-backup.sh      # 技能自动备份
frontier_sources.py       # 自学前沿源（arXiv/PwC/Awesome-AI4AI）
router-ssh-enable.sh      # 路由器免密
lan-mac.sh                # 局域网 Mac 管控
```

---

## §9 验证清单（逐项打勾）

```bash
# 1. Hermes 本体
hermes --version                    # ✓ v0.23.2+
curl -s http://127.0.0.1:18789/health  # ✓ gateway 活着

# 2. 技能
find ~/.hermes/skills -name SKILL.md | wc -l   # ✓ 359（272 主仓库 + 87 外部）

# 3. 配置
hermes status --full                # ✓ provider / 平台全 connected

# 4. 记忆
sqlite3 ~/.hermes/memory_store.db 'select count(*) from facts;'  # ✓ ~439

# 5. cron
hermes cron list                    # ✓ 12 个任务

# 6. 密钥
python3 -c "import os; print(len([l for l in open(os.path.expanduser('~/.hermes/.env')) if '=' in l]))"  # ✓ 116

# 7. 设备
adb devices -l                      # ✓ MI8 + 平板
~/pad-type "恢复测试"               # ✓ 平板输入框出现中文

# 8. 脚本
ls ~/.hermes/scripts | wc -l        # ✓ 263
```

---

## 已知不迁移项（无需恢复）

- `cache/`（pnpm/uv 缓存，重装会自动重建）
- `chrome-profile-mirror/`（登录态镜像，需在新机重新登录）
- `sessions/`（历史会话，可丢弃）
- `state.db`（运行态，自动重建）

## 维护记录

- 2026-11-23：初版，基于本机实测。GitHub 备份仓库只含 skills/，其余需手动迁移。
