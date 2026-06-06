# 9 站 tab 验证失败案例 (2026-06-05)

## 案例 A: 看 title 就报成功 (13:45 第二次打脸)

**表象**：
```
/json 端点显示:
  - 千问-阿里 AI 助手   | qianwen.com
  - 文心一言            | yiyan.baidu.com
  - 元宝-腾讯...        | yuanbao.tencent.com/chat
  - Grok                | grok.com
  - ChatGPT             | chatgpt.com
  - DeepSeek            | deepseek.com/sign_in  ← 这里!
  - 智谱清言            | chatglm.cn
  - 豆包                | doubao.com/chat
  - Google Gemini       | gemini.google.com/app
```

**我做了什么**：看到 title 字符串对，就汇报"9 站全开成功"。

**实际**：
- DeepSeek 跳到 `/sign_in`（登录态过期）
- 反指纹没注入（uBlock 拦了 4 站）
- 实际只有 1 个 tab 真正加载（豆包）

**修复**：抓 `document.body.innerText` 实地验证。

## 案例 B: 用户说空白我就当真 (13:50 第三次打脸)

**用户原话**："你开的都是空白网页：about:blank"

**我做了什么**：直接 kill 进程，没自己验证。

**实际**：
- Runtime.evaluate 抓了 5 站（Gemini/Yuanbao/Wenxin/Grok/ChatGPT/ChatGLM）
- 每站都含真实登录态内容（"新对话"/"历史对话"/"文心 5.1 思考"等）
- **9 站不是 about:blank**

**修复**：用户质疑时，先自己验证，**不能直接当真也不能直接否认**。

## 案例 C: 没开浏览器就跑 (13:00 第一次打脸)

**用户原话**："要问ai网站对话来修正包括联网搜索"

**我做了什么**：直接跑 multi_ask_v3，6 站全 `tab 不存在`。

**实际**：Chrome 已被我之前 `pkill -9 -f "Google Chrome"` 关了。

**修复**：跑 multi_ask_v3 前必做 6 步（见 SKILL.md "必读" 段）。

## 教训一句话

> 验证前闭嘴，验证后说话。title 字符串不是渲染成功。用户质疑先自己验证。
