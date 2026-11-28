# 从聊天粘贴重建 YAML：recipe

用户把运行时配置（Runtime Profile）分批贴到聊天里时，文本会被截断、长行会顶格化丢失缩进。目标：产出一份可直接导入的 `.yaml`。

## 流程

1. **落盘原文**：把用户贴的每批文本写到 scratch 文件（如 `~/.hermes/cache/scratch/ad_rules_batchN.txt`），不直接在聊天文本上改。
2. **提取规则**：按行正则提取，**保留规则类型**，去重保序：
   ```python
   m = re.search(r'^\s*-\s*"(DOMAIN(?:-SUFFIX|-KEYWORD)?|IP-CIDR),([^"]+)"', line)
   if m: rules.append(m.group(1) + "," + m.group(2))
   ```
   - `IP-CIDR` 规则要补 `,no-resolve`。
   - `DOMAIN` / `DOMAIN-SUFFIX` / `DOMAIN-KEYWORD` 不能混为一谈，否则匹配行为变了。
3. **压缩同根随机子域**：几百条形如 `某随机串.adobestats.io` 的 `DOMAIN` 精确规则，用 `DOMAIN-SUFFIX,adobestats.io` 一条通配替代，覆盖等价。`adobe.com` 这类非随机根域如果原本有精确规则也要保留对应通配。
4. **插入基础配置**：拿一份已知可用的配置做底（节点、策略组、DNS、TUN 段），在规则锚点（如 `RULE-SET,geoip-ruleset-cn`）前插入提取出的规则块。
5. **验证**：
   ```python
   import yaml
   d = yaml.safe_load(s)
   print(len(d['proxies']), len(d['proxy-groups']), len(d['rules']))
   ```
   同时确认 `dns:` / `tun:` 段完整、测速地址统一、没有残留 `strict-route`（iOS 场景）。
6. **交付**：写到 `~/Downloads/` 之类用户能找到的目录，用 `MEDIA:/绝对路径` 发文件；正文只报实测计数和改了什么，不 dump 配置内容。

## 关键坑

- **`read_file` 默认只返回 2000 行**，会静默截断。重建长配置时若用它读，再写回会丢尾部段落。用：
  ```python
  with open(path, encoding="utf-8") as f:
      s = f.read()
  ```
- 聊天粘贴的 emoji 转义（形如 `\U0001F6D1`）在 YAML 双引号内可直接保留，也可转成实际 emoji，两种都能解析。但顶格的行必须重新补 4 空格缩进，否则 YAML 解析失败。
- 用户分批贴时，前一批可能被截断（比如只到某个域名就断了）。交付时明确说清「还差哪一段」，让用户决定继续贴还是接受当前覆盖度；不要假装完整。
- 配置里若有 `external-controller` 的 `secret`，它已经在聊天里暴露过，交付前换新。
- 用户贴的配置含节点密码/UUID，属敏感信息；只在这个私聊处理，提醒别转发。
