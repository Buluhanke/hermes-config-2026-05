# iOS 客户端与 Clash Mi 细节

## 选型判断

- **Clash Mi**：免费、GPL-3.0、内置真 Mihomo 内核、KaringX/clashmi、约 10.6k star。配置与路由器 OpenClash 同款，可直接搬。iOS 15+。从非国区 App Store 或 TestFlight 装。
- **Stash**：付费（美区约 $5.99）、闭源、自研引擎、官方称兼容 Clash Premium 配置。iOS 16+。适合要覆写、精致 UI、愿意付费的用户。Mihomo 新字段可能晚一步跟进。
- 同平台还有 Karing / Hiddify（免费、sing-box 系）、Shadowrocket（付费、自有格式）。

## Clash Mi 真实菜单（别照抄第三方教程）

第三方教程常写「设置 → DNS」，实际当前版本：

- **延迟测试 URL / UserAgent**：在「应用设置」。默认 `https://www.gstatic.com/generate_204`，改成国内可达的 204 地址。
- **DNS / TUN**：在「核心设置」。每个块（TUN、DNS、NTP、TLS、Sniffer、LAN）有独立 `Overwrite` 开关——**不开覆写时这些项跟随订阅配置，改不了也看不到**。要自定义必须先开对应块的 Overwrite。
- **导入配置**：「我的配置」→ 右上角 ＋ → 添加配置链接 / 扫描二维码 / 导入配置文件。加完要**点选该配置**才会启用，光添加不算。
- **诊断**：首页有「面板」（zashboard）、「Runtime Profile」（只读，看最终实际跑的配置）、「Network Check」（DNS / HTTP-TUN / HTTP-Proxy / 路由表四步定位）。

## 覆写机制（三层）

```
订阅配置  ←  自定义覆写  ←  Clash Mi 内置覆写
```

- 有自定义覆写：自定义覆写覆盖订阅 → 生成配置1 → 内置覆写再覆盖配置1。
- 无自定义覆写：内置覆写直接覆盖订阅。
- 想完全按机场订阅来（避免 App 设置改掉调好的 DNS/TUN）：导入时选「内置-不覆写」，或订阅链接后加 `overwrite=false`。
- 自定义规则用「编辑配置」里的覆写，不要直接改订阅——更新订阅会冲掉。

## iOS 专属坑

- iOS 对 VPN 扩展有约 **50MB 内存上限**，超了系统会杀 VPN 进程，表现为「点连接后立刻自动断开」。解法：减少 geosite/geoip/ip-asn 规则数量，改用 mrs 格式规则集。
- TUN 网络栈在 iOS/macOS 只能用 `gvisor`（桌面才有 `system` / `mixed`）。
- 收不到 Telegram / Instagram / X 推送：核心设置 → TUN → 开 `includeAllNetworks`，关 `excludeLocalNetworks` / `excludeCellularServices` / `excludeAPNs`；或在编辑配置里启用「附加 Apple 推送通知规则」。
- 部分 App 无网络 / 网易新闻视频播不了：关掉核心设置 → TUN 的「附加 HTTP 代理到 VPN」。
- 同一时间只有一个 VPN 生效；装多个代理 App 会互相顶掉。
- 从 Wi-Fi 切蜂窝后不通：把连接开关关一次再开。
- 蜂窝下自动选节点要节制：`interval` 拉长 + `lazy`，否则持续测速吃套餐流量。
