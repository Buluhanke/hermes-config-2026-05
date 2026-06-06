# du 磁盘占用拆解 SOP

## 适用场景

用户问"X 占多大 / 这么大合理吗 / 怎么瘦身"时，**不要直接信直觉答**，按本 SOP 走，5 秒内给出"哪几个真大头 + 哪个用户能安全删"的精准报告。

## 标准 3 步流程

```bash
# 步骤 1: 顶层总大小
du -sh /path/to/X

# 步骤 2: 内部 TOP 15
du -sh /path/to/X/* | sort -hr | head -15

# 步骤 3: 找用户真正关心的"小但重要"的文件（登录态/cookies/db）
ls -la /path/to/X/Default/Cookies \
       /path/to/X/Default/Local\ Storage/ \
       /path/to/X/state.db
```

## 输出模板（用户最易懂的格式）

```
❌ 错误（基于直觉答）：
"5.6GB 全是登录态，清掉要重登 6 个站" ← 用户崩溃

✅ 正确（拆解后答）：
| 真实大头 | 大小 | 是啥 | 跟登录态有关？ |
| OptGuideOnDeviceModel | 4.0GB | Chrome 152+ Gemini Nano 本地大模型 | ❌ 无关 |
| Default/Cookies | 几KB | 6 个站登录态 | ✅ 真正担心的小文件 |
| Default/其余 | 800MB | 浏览器配置/历史/缓存 | 部分 |
| ... | ... | ... | ... |

→ 用户一眼看懂：5.6GB 里 4GB 是另一个东西，跟登录态无关
```

## 真实案例：chrome-debug 5.6GB

用户原话：*"chrome-debug 5.6GB 6 个 AI 站登录态+缓存"*

**我第一反应（错）**："清掉要重登 6 个 AI 站" ← 误导，用户以为登录态占 5.6GB

**拆解后（对）**：
- `OptGuideOnDeviceModel` 4.0GB — Chrome 152+ 内置 Gemini Nano 本地 LLM
- `Default/Cookies` 几KB — 6 个站登录态真正大小
- `Default` 800MB — 普通浏览器配置/历史
- **结论**：5GB 是无关模型，可独立删；登录态只 < 10MB

## 适用目录清单（macOS 常见"为啥这么大"）

| 目录 | 常见大头 | 真的能删吗 |
|---|---|---|
| `~/.hermes/chrome-debug` | Gemini Nano / Safe Browsing / 浏览器缓存 | 大头可删，登录态保护好 |
| `~/.hermes/hermes-agent/venv` | PyTorch / transformers / 各种包 | ❌ 删了主体跑不起来 |
| `~/.hermes/state.db` | 会话历史 | 备份后可清空 |
| `~/Library/Caches` | 各 App 缓存 | 全可删，App 启动会重建 |
| `~/Library/Developer/Xcode/DerivedData` | 编译中间产物 | ✅ 删了 Xcode 重新编译 |
| `~/Library/Group Containers` | iCloud/同步缓存 | 部分可清 |
| `~/.docker` | 悬空镜像/容器 | `docker system prune -a` |
| `node_modules` | 各包依赖 | 删了 `npm install` 重建 |
| `~/.git/objects` | 大文件历史 | `git gc` + BFG 清理 |

## 关键 SOP 心法

1. **先拆解，再判断** — 大空间问题 90% 的真相在第 2 步（TOP 15）就出来了
2. **用户担心的 = 小文件** — 登录态、配置文件、database，往往 < 10MB
3. **用户没注意的 = 大文件** — 系统自带、模型、缓存、临时
4. **把"大头无关"和"小头相关"对比列** — 用户立刻明白哪些安全可删
5. **不要硬猜** — 5 秒的 du 顶 5 分钟的脑补

## 配合规则

- `proactive-execution` 规则15（先识别具体对象再答）
- `proactive-execution` 规则8（不要绑定特定工具/服务）
