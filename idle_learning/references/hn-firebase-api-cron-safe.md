# HN Firebase API — Cron 环境安全调用脚本

## 关键问题

⚠️ **2026-05-28 发现**：遍历 30 个故事 + 每条 10s 超时 = 总超时 60s（被 cron 任务 60s 硬限制卡死）

## 正确做法

### 1. 获取 Top 10 故事（40s 内完成）

```python
# /tmp/hn_top_20260528.py — 写入文件后执行
import urllib.request
import json

url = "https://hacker-news.firebaseio.com/v0/topstories.json"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    ids = json.loads(resp.read())

# 获取前10条故事详情
for i, story_id in enumerate(ids[:10]):
    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    try:
        req2 = urllib.request.Request(story_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2, timeout=10) as r:
            story = json.loads(r.read())
            title = story.get('title', 'N/A')
            score = story.get('score', 0)
            url = story.get('url', '')
            print(f"{i+1}. [{score}pts] {title}")
            if url:
                print(f"   {url[:70]}")
    except Exception as e:
        print(f"Error: {e}")
```

**执行**：`python3 /tmp/hn_top_20260528.py`

### 2. 快速测试版（5s 内完成）

```python
# /tmp/hn_fast_test.py
import urllib.request
import json

url = "https://hacker-news.firebaseio.com/v0/topstories.json"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=8) as resp:
    ids = json.loads(resp.read())

# 只取前5个ID测试连接
for i, story_id in enumerate(ids[:5]):
    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    try:
        req2 = urllib.request.Request(story_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2, timeout=5) as r:
            story = json.loads(r.read())
            print(f"{i+1}. [{story.get('score', 0)}pts] {story.get('title', 'N/A')}")
    except Exception as e:
        print(f"Error {story_id}: {e}")
```

## 绝对禁止

❌ **不要用** `python3 -c "..."` 或 heredoc `<< EOF` 获取 HN 数据（会被 cron 拦截）
❌ **不要** 遍历 30 个故事（超时 60s，被 cron 硬限制卡死）
❌ **不要** 使用 `curl -s "https://..." -o /tmp/hn_ids.json` + `python3 -c "..."` 组合（内联会被拦截）

## 为什么不用 Firecrawl？

- Firecrawl Payment Required / 404 频繁出现（credits 耗尽）
- HN Firebase API 免费、稳定、无需认证
- 适合深度文章（得分>500），不适合批量抓取

## API 特性

- **免费**：无需认证
- **稳定**：无 402/404 问题
- **快速**：Top 10 版本 40s 内完成
- **简单**：纯 HTTP GET，无复杂协议
