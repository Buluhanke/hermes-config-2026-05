# Scrapling 网页解析工具研究（2026-06-02）

## 验证结论

**安装**：`~/.hermes/hermes-agent/venv/bin/pip3 install "scrapling[all]"`

**验证状态**：✅ 已装可用

## 核心能力

| 能力 | 说明 |
|------|------|
| 自适应解析 | 网站结构变化时自动重定位元素，不依赖固定CSS选择器 |
| StealthyFetcher | curl_cffi底层，模拟真实浏览器TLS指纹 |
| Cloudflare绕过 | 能过其他平台的Cloudflare（1688除外） |
| MCP服务器 | 可作为MCP工具被其他Agent调用 |
| 代理轮换 | 内置代理池集成 |

## 1688实测结果

**结果**：❌ 无法绕过1688登录墙

- Scrapling隐身抓取仍被301重定向到 `login.taobao.com`
- 根因：1688登录检测基于阿里系Cookie，不是TLS指纹问题
- 任何工具都无法绕过1688登录墙，主力方案是**已登录Chrome CDP session**

## 有效场景

- 阿里巴巴国际站（无登录墙）
- 慧聪网（hc360.com）
- 中国制造网（made-in-china.com）
- 其他中文B2B平台
- Cloudflare保护的普通网站

## 测试脚本

- `/tmp/1688_scrapling.py` — 基础功能测试
- `/tmp/1688_parse.py` — 自适应解析测试
- `/tmp/1688_product_test.py` — 商品详情页测试

## 与browser CDP的关系

Scrapling是**备用方案**，browser CDP是**主力方案**。

| 场景 | 方案 |
|------|------|
| 1688采购 | 已登录Chrome CDP |
| 其他B2B平台 | Scrapling优先 |
| Cloudflare保护站 | Scrapling尝试 |
| 结构稳定网站 | Scrapling自适应 |

## LG-token-saver反面教材

**推广信息**：`npx skills add jnbno1163/LG-token-saver`

**验证结果**：❌ 虚假命令
- GitHub仓库确实存在（1★，昨天创建）
- 但`npx skills add`是**Claude Code专用命令**，Hermes无效
- Claude Code与Hermes是不同的AI编程工具，安装命令不通用

**教训**：收到推广信息先验证安装命令是否针对正确的工具，不盲目转发。
