# Clash Mi 备份 zip 编辑

用户导出整份 Clash Mi 备份（zip 内 `profiles.json` + `setting.json` + `service_core_setting.json` + `profiles/*.yaml`）并要求「改这份」时用本流程。

## 流程

1. **解压到 scratch**，不动上传的原文件。
2. **定位生效 profile**：读 `profiles.json` 的 `current_id` 找当前启用的 yaml（备份常含 5–6 份 profile，只有一份生效）；`remark` 只是显示名。改错 profile 等于白改。
3. **节点一致性校验**：把优化配置的 `proxies` 按 `(name, server, port)` 集合与生效 profile 比对，集合不同就先解决节点来源——直接替换会让全部节点失效。
4. **按根域压缩垃圾子域**：几百条 `随机串.adobestats.io` 压成 `DOMAIN-SUFFIX,adobestats.io`；同类 `adobe.io` / `hstatic.io` 各一条通配。用脚本按根域查是否已覆盖，别靠肉眼判断，更不要把 `adobe.com` 归到 `adobestats.io`。
5. **补回功能规则**：从**原始订阅**里按策略组名提取 `🚀 节点选择` 与 `☁️ CloudFlareCDN` 的规则，去重后插到 `MATCH,` 之前。这两类是流媒体解锁与 CF 直连，不是冗余；`RULE-SET,geoip-ruleset-cn` 只替代国内 IP 直连。
6. **对齐 secret 与测速地址**：secret 取 `service_core_setting.json`；`profiles.json` 中生效 profile 的 `delay_test_url` 与 `setting.json` 的全局 `delay_test_url` 都改成国内 204 地址，并 grep 有无尾随中文句号等杂字符。
7. **验证 + 打包**：`yaml.safe_load()` 打印 proxies/groups/rules 计数、确认末条是 `MATCH,`、无重复策略组名；用 `zipfile` 重打包保持所有相对路径，`testzip()` 返回 None 才算通过。
8. **交付**：`MEDIA:/绝对路径` 发一次文件，正文只报实测计数和启动注意事项。

## 坑

- **策略组重复名**：Clash Mi iOS 内置会创建 `Apple Push Notification` 组，配置里再定义同名组 → `VpnError:LibclashStart failed: ProxyGroup Apple Push Notification: duplicate group name`，App 直接起不来。删掉自定义 APN 组，把引用它的规则改走 `🎯 全球直连`。
- **启动报错先看策略组**：用户截图报 LibclashStart failed 时，先 dump `proxy-groups` 名字做 Counter 查重，别先怀疑节点或 DNS。
- **profile_patchs.json 的 `append_apple_push_rules`** 为 true 时 App 会自行追加 APN 规则；与自定义 APN 组叠加也会冲突。
- **secret 对齐**：优化配置里的 secret 若与备份全局 secret 不同，外部控制器连不上；写回前从 `service_core_setting.json` 读实际值。
- **只回文件**：用户发的是「改压缩包」，不是要分析报告；长解释和重复发同一文件是明确的体验失败。
