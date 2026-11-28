---
name: clash-mihomo-config
description: Clash/Mihomo 订阅与客户端配置。Use when 问 Clash 订阅、客户端或配置。
---

# Clash/Mihomo 配置管理

代理类任务先定三件事：平台、配置来源（订阅 URL 还是本地 YAML）、是否涉及第三方转换或隐私。顺序错了会做无用功。

## 一、客户端选型（先定平台再动手）

| 平台 | 首选 | 备选 | 关键差异 |
| --- | --- | --- | --- |
| iOS/iPadOS | Clash Mi（免费、GPL-3.0、内置 Mihomo） | Stash（付费、闭源、兼容 Clash Premium） | Clash Mi 用真 Mihomo 内核，配置跟路由器同款可直接搬；Stash 是闭源自研引擎，对 Mihomo 新字段兼容更差 |
| Android | Clash Meta for Android / FlClash | — | 原生 Mihomo 配置 |
| 路由器 | OpenClash / Nikki | — | 插件设置由路由固件管理，配置走 YAML |

非国区 Apple ID 才能装这类 App；只从官方商店/官网装，拒绝企业证书或描述文件版。

## 二、订阅隐藏与风险（回答隐私类问题前必判）

核心事实：第三方订阅转换只隐藏客户端 URL 参数，服务端仍持有你的**明文订阅 URL、token 和完整节点列表**，且有能力改写返回配置。HTTPS 只保护传输，不保护服务端日志。token 短链只防旁人，不防服务方。

- 真要隐私：自建（Cloudflare Worker 一键 Deploy，或本地 Docker 版 subconverter 绑 `127.0.0.1`）。
- 只是不想在聊天/截图里暴露链接：token 短链够用。
- psub 类 CF Worker 反代方案（随机化节点 IP/密码后再交给公共转换后端、拿回结果再还原）能避开公共后端看到真实节点，但要自己部署。

详见 `references/subscription-privacy.md`。

## 三、Clash YAML 配置：always-on 规则

- 测速地址用国内可达的 `generate_204`（如 `http://connect.rom.miui.com/generate_204`），不要用 `gstatic`——后者在蜂窝网络下常超时，会把全部节点判死。
- `url-test` 的 `interval` 至少 120 秒并开 `lazy: true`，`tolerance` 50~100ms。频繁测速既耗套餐流量，也可能触发机场限速。
- iOS 的 TUN `stack` 只能用 `gvisor`；去掉 `strict-route`，它在 iOS 下容易破坏局域网访问和 Apple 推送。
- DNS 用 `enhanced-mode: fake-ip`；蜂窝场景关 `dns.ipv6`，避免 AAAA 查询拖慢解析和 IPv6 绕过隧道。
- 大量同根随机子域（某某.adobestats.io 之类）用一条 `DOMAIN-SUFFIX,<根域>` 通配替代——覆盖等价且省内存。iOS VPN 扩展有约 50MB 内存上限，超了会「一点连接就秒断」。
- 精简只压同根随机垃圾子域；`🚀 节点选择`（流媒体解锁）、`☁️ CloudFlareCDN`（CF IP 直连）、`GEOIP,CN` 是功能规则，删了会让流媒体不解锁或 CF 站点异常。`RULE-SET,geoip-ruleset-cn` 只替代国内 IP 直连，不替代流媒体解锁规则。
- 判断覆盖要按根域实测查 `DOMAIN-SUFFIX,<根域>`，别把 `adobe.com` 当成 `adobestats.io` 的子域；`adobe.com` 只有精确规则时，新的 `*.adobe.com` 子域要单独补。
- Clash Mi iOS 内置会创建 `Apple Push Notification` 组；配置里再定义同名组会 `LibclashStart failed: ProxyGroup Apple Push Notification: duplicate group name`，App 起不来。删自定义组，把 APN 规则改走直连组。
- 测速地址两处都要查：`profiles.json` 每 profile 的 `delay_test_url`（可能混进尾随中文句号）和 `setting.json` 全局 `delay_test_url`（可能还是 gstatic）。尾随杂字符会让测速静默失败。
- 配置一旦贴进聊天或公开渠道，`external-controller` 的 `secret` 必须换新。
- 改完配置必须 `yaml.safe_load()` 解析并打印 `proxies/groups/rules` 计数，不要凭肉眼判断。

## 四、从粘贴片段重建配置（Procedure）

用户从聊天贴配置时，长内容会被截断、部分行会顶格化丢失缩进。按此顺序处理：

1. 原文落盘到 scratch，不直接改聊天文本。
2. 按正则提取每条规则，**保留规则类型**（`DOMAIN` / `DOMAIN-SUFFIX` / `DOMAIN-KEYWORD` / `IP-CIDR`），去重保序；`IP-CIDR` 规则要带 `no-resolve`。
3. 压缩同根随机子域为通配规则。
4. 以一份已知可用的基础配置为底，在规则锚点（如 geoip RULE-SET）前插入提取出的规则块。
5. `yaml.safe_load()` 验证 + 打印计数 + 确认 dns/tun 段完整，再交付文件。

**坑：读长配置文件不要用 `read_file`**——它默认只返回 2000 行，会静默截断；若基于截断内容写回，尾部段落（dns/tun 等）会丢失。用 Python `with open(path, encoding="utf-8") as f: s = f.read()` 读全文。

**坑：粘贴文本里的 emoji 转义**（形如 `\U0001F6D1`）在 YAML 双引号内可直接保留或转成实际 emoji，两种都能解析。

## 五、Clash Mi 菜单路径（别照抄第三方教程）

第三方教程常写「设置→DNS」，实际版本里 DNS/TUN 在「核心设置」，且要先打开该块的 Overwrite 开关才能编辑。菜单路径和覆写机制见 `references/ios-clients.md`。

## 六、用户发备份 zip 要求改配置

**交付格式铁律**：只回改好的成品文件链接（`MEDIA:/绝对路径`），不写长解释、不重复发同一份文件、不 dump 配置内容。用户明确嫌啰嗦过。

完整流程（定位生效 profile、节点一致性、secret 对齐、重打包校验）见 `references/backup-zip-edit.md`。

## 参考

- `references/backup-zip-edit.md` — Clash Mi 备份 zip 编辑流程：生效 profile 定位、节点校验、功能规则补回、重打包
- `references/ios-clients.md` — iOS 客户端对比、Clash Mi 真实菜单与覆写机制、50MB 内存坑、Apple 推送
- `references/subscription-privacy.md` — 订阅隐藏方案对比与中间人风险
- `references/yaml-rebuild.md` — 从聊天粘贴重建 YAML 的完整 recipe
