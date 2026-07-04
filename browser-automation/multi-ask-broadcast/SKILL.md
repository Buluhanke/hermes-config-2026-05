# multi-ask-broadcast — 多AI站并行广播

## 触发词
"问所有AI" / "广播问题" / "多AI对比" / "交叉验证" / "broadcast"
"同时问" / "问各个AI" / "收集多个AI的意见"

## 用法
```bash
# 基本广播
python3 ~/.hermes/scripts/broadcast.py

# 查看广播状态
python3 ~/.hermes/scripts/broadcast_status.py

# 某站失败时fallback
python3 ~/.hermes/scripts/broadcast_fallback.py
```

## 已登录站点
- ChatGPT (chatgpt.com)
- Gemini (gemini.google.com)
- Doubao (doubao.com)
- ChatGLM (chatglm.cn)
- DeepSeek (chat.deepseek.com)
- Grok (grok.com)

## 与 hermes -z 的区别
- hermes -z：单模型快速回答
- broadcast：6个AI并行，结果对比验证

## 结果处理
广播完用 extract_multi.py 合并结果，写入 fact_store 做知识沉淀
