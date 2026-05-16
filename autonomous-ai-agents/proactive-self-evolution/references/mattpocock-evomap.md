# mattpocock/skills + EvoMap 参考资料

## mattpocock/skills (83k stars, MIT)

GitHub: github.com/mattpocock/skills

### 已安装到 ~/.hermes/skills/mattpocock/

**Productivity 类：**
- `caveman` — 极简压缩沟通，token省75%。触发词："caveman mode"/"talk like caveman"/"less tokens"/"be brief"
- `grill-me` — 深度需求拷问，开始工作前强制追问直到所有决策分支清晰
- `handoff` — 交接文档打包，compact conversation → handoff document for next agent
- `write-a-skill` — 创建新skill的模板和结构规范

**Engineering 类：**
- `diagnose` — 调试循环：reproduce → minimise → hypothesise → instrument → fix → regression-test
- `tdd` — 红绿重构TDD循环，vertical slices
- `improve-codebase-architecture` — 定期救赎乱代码（每几天跑一次）
- `zoom-out` — 代码段放到全系统视角看
- `triage` — issue通过状态机分类

### 安装方式（正确方式）

mattpocock/skills 有 9 个独立 skill，每个必须单独一个目录 + SKILL.md，不能合并文件也不能复制到错误路径。

```bash
# 1. clone 到临时目录
git clone https://github.com/mattpocock/skills.git /tmp/mattpocock-skills

# 2. 在 hermes skills 下建 mattpocock 目录
mkdir -p ~/.hermes/skills/mattpocock

# 3. productivity 类（4个）
for skill in caveman grill-me handoff write-a-skill; do
  cp -r /tmp/mattpocock-skills/skills/productivity/$skill ~/.hermes/skills/mattpocock/
done

# 4. engineering 类（5个）
for skill in diagnose tdd improve-codebase-architecture zoom-out triage; do
  cp -r /tmp/mattpocock-skills/skills/engineering/$skill ~/.hermes/skills/mattpocock/
done
```

**注意**：复制整个目录（含 SKILL.md），不是单独复制 .md 文件到根目录。错误的安装方式会导致 skill 无法被 Hermes 识别调用。

### caveman 示例

**Before:**
> "Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by..."

**After:**
> "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

### grill-me 核心原则
- 不接受模糊需求，直到所有决策分支都清晰
- 每一分支追问：边界条件？极端情况？依赖项？
- 直到用户说"没了，开始吧"才开始执行

---

## EvoMap/evolver (7.4k stars, GPL-3.0)

GitHub: github.com/EvoMap/evolver
官网: evomap.ai

### 核心概念
**GEP (Genome Evolution Protocol)** — 把prompt优化变成可审计、可复用、可遗传的Gene资产

三种资产：
- **Gene**: 能力基因，可遗传
- **Capsule**: 封装的能力包
- **Event**: 演进事件，审计日志

### 策略预设
| 策略 | 创新 | 优化 | 修复 | 适用场景 |
|------|------|------|------|----------|
| `balanced` | 50% | 30% | 20% | 日常运行 |
| `innovate` | 80% | 15% | 5% | 系统稳定，快速上新功能 |
| `harden` | 20% | 40% | 40% | 大改动后，聚焦稳定性 |
| `repair-only` | 0% | 20% | 80% | 紧急修复模式 |

### 安装
```bash
npm install -g @evomap/evolver
evolver --help
```

### 对Hermes的意义
1. Gene概念可借鉴：把成功的prompt优化记录为Gene，追踪演进路径
2. 演进审计日志可以追踪自己的进化历史
3. 平台无关，任何AI Agent都能接入

### 待跟进
- [ ] 研究Gene如何应用到Hermes自我进化
- [ ] 读取GEP协议文档
- [ ] 安装EvoMap CLI ✅ (2026-05-15)

---

## Firecrawl (已部署)

GitHub: github.com/mendableai/firecrawl
文档: docs.firecrawl.dev

AI网页爬虫，能把整个网站转成markdown。

### 当前状态
- **需要 OPENAI_API_KEY** 才能启动 AI 功能（未配 key 前 docker 会卡在启动状态）
- 已部署到 docker，用预构建镜像 `ghcr.io/firecrawl/firecrawl`，无需从源码 build
- 容器未成功启动，原因：缺少 OPENAI_API_KEY 环境变量

### 部署步骤
```bash
# 1. 预构建镜像，不需要 clone 源码
# 写 docker-compose.yaml：
services:
  firecrawl:
    image: ghcr.io/firecrawl/firecrawl:latest
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}   # 必须有此环境变量
    ports:
      - "3002:3002"

# 2. 启动（前台看日志）
docker compose -f /tmp/firecrawl/docker-compose.yaml up

# 3. 验证
curl http://localhost:3002/health
```

### 对1688采购的价值
直接抓取商品详情页、供应商页面，转markdown存档比截图更高效

---

## 关键学习：用户进化原则（2026-05-15确立）

用户的核心要求：
1. **不等指令**：空闲时间主动搜索学习，不待机
2. **全网搜索**：GitHub/arXiv/HN/技术博客 + 浏览器AI对话，不依赖模型知识
3. **白天轻量**：浅搜快扫，5分钟内，重大突破才打扰
4. **夜间深度**：深度搜索+AI对话+结合已有技能，锚定真人化路线
5. **持续进化**：每时每刻都在长脑子，不只是cron任务

这是真人化的本质：不等老板，自己知道什么时候该学。
