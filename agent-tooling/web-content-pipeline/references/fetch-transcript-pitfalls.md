# fetch_transcript.py 实战踩坑 (2026-06-27 真实跑通)

## ✅ 真验证

```bash
python3 ~/.hermes/scripts/fetch_transcript.py \
  "https://www.youtube.com/watch?v=aircAruvnKk" --lang=en --json
```

**结果**: 286 snippets, 完整字幕 + 时间戳, 第一条 "This is a 3."

## 🐍 踩坑 1: YouTube 限速 429

**症状**: `yt-dlp --write-auto-sub` 下载字幕报 `HTTP Error 429: Too Many Requests`

**根因**: YouTube 限速（同 IP 高频请求）

**修法**:
1. `youtube-transcript-api` (Python lib) 走另一条 API 路径，**不 429**
2. 限速重试：加 `--retries 3 --retry-sleep 5` 间隔
3. 换 IP（VPN/proxy）—— fetch_transcript 暂未实现

**当前 fallback 链**:
```
fetch_transcript (youtube-transcript-api) → yt-dlp 字幕 → agent-reach transcribe (Whisper)
```

## 🐍 踩坑 2: B 站 yt-dlp cookie 限制

**症状**: 部分 B 站视频字幕需要登录态

**修法**:
- `yt-dlp --cookies-from-browser chrome` 复用 Chrome 登录态
- 公开视频直接 `yt-dlp --list-subs URL` 拿字幕列表

**当前 fetch_transcript 处理**: 走默认 yt-dlp 配置（不带 cookie），公开视频 OK，登录视频失败

## 🐍 踩坑 3: 语言 fallback 链

**默认**: `--lang=en`
**fallback 链**: fetch_transcript 内部 `languages=[lang, "en"]` —— 你说中文就 `[zh-Hans, zh, en]`

**实际**:
```python
api.fetch(vid, languages=[lang, "en"])  # 第一优先 + 英语兜底
```

## 🐍 踩坑 4: venv 隔离

**问题**: yt-dlp 装在 `~/.agent-reach-venv/bin/yt-dlp`，hermes 自带 venv 没装

**当前处理**: fetch_transcript.py 直接用绝对路径调用：
```python
yt_dlp = Path.home() / ".agent-reach-venv" / "bin" / "yt-dlp"
```

**未做**: 自动 venv 检测 + PATH 修复 —— 不在 fetch_transcript 范围

## 🛠️ fetch_transcript.py 维护

**位置**: `~/.hermes/scripts/fetch_transcript.py`
**行数**: 100 行（含 docstring + 注释）
**依赖**: youtube-transcript-api（hermes venv）+ yt-dlp（agent-reach venv 绝对路径）

**关键 API**:
```python
def fetch_youtube(url, lang="en") -> dict
def fetch_bilibili(url) -> dict
```

**触发词**: "YouTube 字幕 / B 站字幕 / 视频文案 / 字幕提取" → 0 思考走 fetch_transcript.py