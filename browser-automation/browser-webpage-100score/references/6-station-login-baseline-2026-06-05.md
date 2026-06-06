# 6 AI 站登录态基线 — 2026-06-05 18:50

## 背景

用户 2026-06-05 18:50 拍板升级硬规则: **每站必须单独截图 + console 自检验证登录态, 不能假设成功, 失败的单独报告**。

本次 baseline 是 Hermes 第一次用"4 维证据 SOP"实测 6 站登录态, 结果作为未来"AI 站登录态"问题的对照基准。

## Chrome 状态 (验证时刻)

```
Chrome PID 61470: --remote-debugging-port=9333 --user-data-dir=.../Chrome/Default
端口 9333: LISTEN ✓
CDP /json/version: 通 ✓
hermes config cdp_url: ws://127.0.0.1:9333 ✓
```

## 6 站实测数据

| # | 站 | URL | login 态 | username/email | localStorage user-key | cookies | 头像 | 截图路径 |
|---|----|-----|---------|----------------|-----------------------|---------|------|---------|
| 1 | Gemini | gemini.google.com/app | ✅ | K H (hanlukebu@gmail.com) | (Google 账号, N/A) | (N/A) | 自定义 | `browser_screenshot_d19b6026fd794c9189c6511bc59d1e07.png` |
| 2 | 豆包 | doubao.com/chat | ✅ | 用户320735 | (N/A) | (N/A) | 自定义 | `browser_screenshot_5d7d034a0fac440cb421f4752445b248.png` |
| 3 | DeepSeek | chat.deepseek.com | ✅ | 罗 | (N/A) | (N/A) | 自定义 | `browser_screenshot_45f76b0604cf436ba915cbfa6c032992.png` |
| 4 | ChatGPT | chatgpt.com | ✅ | LH (头像缩写) | ✅ `user-LGyeKM5DBTtdLMSeFo4Nddva` | 2757 chars | 自定义 | `browser_screenshot_75754c4c5606446b830acdbd2db3343f.png` |
| 5 | Grok | grok.com | ✅ | lukebu hanlukebu@gmail.com | (N/A) | (N/A) | 自定义 | `browser_screenshot_3092ce3c721e418b9df7143225ee75b0.png` |
| 6 | **智谱清言** | chatglm.cn | ⚠️ **低置信度** | 默认头像 | ❌ 无 (仅 claw_guide_dialog_shown 等引导) | **209 chars** | 默认人物剪影 | `browser_screenshot_669c2029bba84529a96b5a4c5367edb4.png` |

**截图总目录**: `~/.hermes/cache/screenshots/browser_screenshot_*.png` (6 张)

## 智谱清言坑点详解 (重点)

**症状**:
- 右上角是默认人物剪影头像, 无真实头像
- localStorage 4 个 key: `claw_guide_dialog_shown` / `main_chat_guide_new_feature` / `GLM5_1_guide_popover` / `__tea_cache_tokens_20009687` — **全部是引导/缓存, 无 user/uid/token/email 任何登录标识**
- `document.cookie` 长度 209 chars (ChatGPT 2757 / Grok cookies 也在 200+, 但智谱的 209 字符**无明显登录态字段**)
- URL 是 `chatglm.cn/main/alltoolsdetail?lang=zh` 首页能正常加载 (未跳登录页 = 可能已登录但态不全, 或免登录可访问首页)

**3 种可能**:
1. **cookie-only 登录**: session 存在 cookie 但 localStorage 不写 (反之亦然)
2. **旧号残留**: 账号存在但已过期, cookies 没清
3. **未登录访客**: 智谱允许访客用基础功能, 登录态在更深层 (订阅/历史)

**应对**:
- 跑智谱对话前必先用 4 维证据 SOP 复核
- 失败/低置信度**单列报告**, 不与成功挤一行
- 建议用户手动打开智谱清言看右上角是否显示真实账号/手机号

## 4 维证据 SOP 实战模板 (复制可用)

```javascript
// browser_console 注入这段 JS 拿 3 维证据
(() => {
  const storage = {};
  try {
    for (let i=0; i<localStorage.length; i++) {
      const k = localStorage.key(i);
      if (/user|uid|token|account|login|auth|email|profile/i.test(k)) {
        storage[k] = localStorage.getItem(k)?.slice(0, 100);
      }
    }
  } catch(e) {}
  const loginBtn = Array.from(document.querySelectorAll('a, button'))
    .filter(el => /登录|Login|Sign in/i.test(el.innerText || ''))
    .map(el => el.innerText.trim());
  return {
    title: document.title,
    url: location.href,
    localStorageUserKeys: Object.keys(storage),
    cookies_len: document.cookie.length,
    hasLoginBtn: loginBtn.length > 0,
    loginBtnTexts: loginBtn,
  };
})()
```

**判定规则**:
- `localStorageUserKeys.length ≥ 1` → 强证据 (✅ 已登录)
- `cookies_len ≥ 200` 且无 `hasLoginBtn` → 中等证据
- `hasLoginBtn === true` → 反向强证据 (❌ 未登录)
- 3 维全弱 + 默认头像 → ⚠️ 低置信度, 单列报告

## 失败报告模板

```
## 验证结果 (YYYY-MM-DD HH:MM)

✅ N 站全登录: <站名1> / <站名2> / ...
⚠️ M 站低置信度 (待复核): <站名>
   - <症状1>
   - <症状2>
   - 建议: <用户手动确认>
❌ K 站失败: <站名>
   - <症状1>
   - <症状2>
   - 建议: <修复方案>

M 张截图: ~/.hermes/cache/screenshots/browser_screenshot_*.png
```

**关键**: 失败的/低置信度的**单列一行**, 不与成功挤在一行里说 "X/Y 成功"。

## 复现配方 (下次验证用)

```bash
# 1) 验证 Chrome / 端口 / 配置
ps aux | grep -E "Chrome|Chromium" | grep -E "remote-debugging"
lsof -nP -iTCP:9333 -sTCP:LISTEN
curl -s http://127.0.0.1:9333/json/version | python3 -m json.tool
grep "cdp_url" ~/.hermes/config.yaml

# 2) 准备截图目录
mkdir -p /tmp/hermes-login-check/$(date +%Y%m%d-%H%M%S)

# 3) 对每站 4 步 (以 Gemini 为例)
browser_navigate url=https://gemini.google.com/app
browser_snapshot  # 看 AX 树登录后元素
browser_console expression=... # 上面的 3 维证据 JS
browser_vision question="确认登录态 (右上角头像/账号信息)"

# 4) 收集截图路径 → 报告
```

## 未来触发条件

- 用户问"X 站登录了吗 / 还能用吗 / 登录态还在不在"
- 跑 multi_ask_v3 / 9 站交叉问前必跑 (防止历史 tab 早已过期)
- 任何"AI 站对话失败"类问题, 先按 4 维 SOP 验证登录态再排查输入方式
- 智谱清言**特别**: 默认 + cookies 209 是已知低置信度, 对话前必复核
