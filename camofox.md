---
name: camofox
description: "Camofox本地抗检测浏览器服务器——Firefox指纹伪造+持久化Cookie+独立身份Profile"
---

# Camofox Browser

Camofox是基于Camoufox的本地抗检测浏览器服务器，为AI agent提供持久化、高隐蔽性的浏览器自动化。

## 服务状态

Camofox已安装运行：`http://localhost:9377`
引擎：Camoufox（Firefox分支，含指纹伪造）
状态：health端点返回`ok:true`

## 快速验证

```bash
# 健康检查
curl http://localhost:9377/health

# 返回示例：
# {"ok":true,"engine":"camoufox","browserConnected":true,"browserRunning":true,"activeTabs":1}
```

## API基础用法

```bash
# 1. 创建标签页
TAB=$(curl -s -X POST http://localhost:9377/tabs \
  -H "Content-Type: application/json" \
  -d '{"userId":"agent1","sessionKey":"task1","url":"https://example.com"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tabId'])")
echo "Tab ID: $TAB"

# 2. 获取页面快照（含可点击元素ref）
curl -s "http://localhost:9377/tabs/$TAB/snapshot?userId=agent1"

# 3. 点击元素（ref格式：e1, e2, e3...）
curl -s -X POST "http://localhost:9377/tabs/$TAB/click" \
  -H "Content-Type: application/json" \
  -d '{"userId":"agent1","ref":"e5"}'

# 4. 输入文本
curl -s -X POST "http://localhost:9377/tabs/$TAB/type" \
  -H "Content-Type: application/json" \
  -d '{"userId":"agent1","ref":"e2","text":"hello"}'

# 5. 导航
curl -s -X POST "http://localhost:9377/tabs/$TAB/navigate" \
  -H "Content-Type: application/json" \
  -d '{"userId":"agent1","url":"https://github.com"}'

# 6. 搜索宏（内置）
curl -s -X POST "http://localhost:9377/tabs/$TAB/navigate" \
  -H "Content-Type: application/json" \
  -d '{"userId":"agent1","macro":"@google_search","query":"AI agents"}'

# 7. 关闭标签
curl -s -X DELETE "http://localhost:9377/tabs/$TAB?userId=agent1"
```

## 搜索宏支持

| 宏 | 站点 |
|----|------|
| `@google_search` | Google |
| `@youtube_search` | YouTube |
| `@amazon_search` | Amazon |
| `@reddit_search` | Reddit |
| `@wikipedia_search` | Wikipedia |
| `@twitter_search` | Twitter/X |
| `@yelp_search` | Yelp |
| `@linkedin_search` | LinkedIn |

## 持久化配置

在`~/.hermes/config.yaml`中添加：
```yaml
browser:
  camofox:
    managed_persistence: true
```

每个Hermes Profile可映射独立Camofox userId，实现Cookie跨运行保留。

## 与browser-use的关系

- `browser-use`：直连用户Chrome（CDP），继承所有登录态
- `Camofox`：独立浏览器实例，指纹伪造更强，但需要独立管理登录态
- 两者可并行使用：browser-use做日常操作，Camofox做抗检测任务

## 安装位置

- 服务脚本：`~/projects/camofox-browser/server.js`
- 启动命令：`cd ~/projects/camofox-browser && node server.js`
- 启动后后台运行，由Hermes进程管理
