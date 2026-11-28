---
name: tvbox-subscription-setup
description: 找/装/配 TVBox 影视仓自动更新接口源。Use when 要免费影视客户端与订阅源。
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [tvbox, iptv, 影视仓, subscription, media]
metadata:
  hermes:
    tags: [tvbox, iptv, subscription, media]
    related_skills: [android-control, agent-reach]
---

# TVBox 影视源与客户端配置

## When to Use

用户要「免费 TVBox / 影视仓 / 能自动拉接口源的客户端」、要装影视客户端、问接口源会不会失效、要让源自动更新时用本技能。

## 一、核心结论：自动更新来自订阅，不是客户端

「自动获取接口源」= 一个**每日自动重新拉取全网源、探活、去重、排序**的订阅 URL，客户端每次打开重新读它。不要给用户一页静态接口列表让他挨个复制——那种几天后全死。

选源标准（按优先级）：

1. **服务端有定时 CI**（GitHub Actions 每日拉取合并 + 健康检查 + 坏源自动停用/恢复）。
2. **健康分层产物**：区分「推荐（实测能搜能播）」与「全量（含未验证/已死源）」。默认推**推荐版**——全量版近半是死源，导入后体感是「大半点不动」。
3. **多线路并列**：raw / ghproxy / jsDelivr / Pages / Release 至少两条，一线不通换下一条；不押注单一加速服务。

实测可用的订阅（交付前仍要 web_extract 验一次能返回 `{"spider":...,"sites":[...]}`）：

| 订阅 | 地址 |
|---|---|
| 每日 CI + 健康分层（首选） | `https://raw.githubusercontent.com/hebijunge/tvbox-config/main/tvbox_recommended.json` |
| TVBox 官方聚合单仓 | `https://raw.githubusercontent.com/TVboxorg/TVbox/main/dist/official.json` |
| 牛虎单仓（含直播/网盘） | `https://raw.githubusercontent.com/niubihu1/tvbox/main/1.json` |

国内直连 raw 慢时前缀 `https://ghproxy.net/`。站点随时失效，交付时说明「不保证长期有效、失效换备用线路」。

## 二、客户端选型

| 平台 | 客户端 | 备注 |
|---|---|---|
| Android / 电视盒子 | TVboxOSC（开源免费无广告，内置在线订阅） | 包名 `com.kukuqi.tvbox.osc`（旧版是 `com.mygithub0.tvbox0.osdX`，两版可并存） |
| Windows 桌面 | TVBox Desktop | 装完自带内置订阅，无需找源 |
| 手机/多仓 | 影视仓 / FongMi | 支持仓库切换、在线更新 |

## 三、配置订阅（TVboxOSC 实测路径）

1. 「我的」→「点播源」→ 右上角 `+` →「添加订阅」。
2. 填「自定义订阅名」，在「地址」框填完整 URL，勾「使用此订阅」→「添加」。
3. 验证：列表里该订阅被勾选且地址完整；首页/搜索能出影片（如搜「流浪地球」返回影片列表）。首页若提示「当前站点没有提供首页推荐」属正常——订阅默认站点可能不带首页推荐，不影响搜索/点播。
4. 源失效后的处理：重启 App 会重新拉订阅；整条订阅挂了就换 ghproxy / jsDelivr / Release 备用地址。

## 四、坑

- **接口源必然失效**：采集站关停、换域名、防盗链失效是常态。回答「会不会失效 / 能不能自动更新」时明确分两层：服务端订阅 CI 每日自愈（自动剔除死源、恢复活源），客户端每次打开重拉配置；单个站点彻底关停是「换成别的站」而非修好，且客户端有缓存需重启才拿到新名单。
- **输入框坐标会随软键盘弹起整体上移**：弹窗里第一个框填完，软键盘弹出后第二个框位置大幅改变；填下一个框前重新 dump bounds，否则文字串进上一个框。
- **长 ASCII URL 输入**：ADBKeyboard 的 `ADB_INPUT_TEXT` 广播在定制 App 里可能只落地前缀（长 URL 截成 `https://gh`）。切回系统自带输入法用 `input text '<完整URL>'`，dump 读回全文核对。
- **装 APK 到华为设备**：EMUI 对「PC 工具安装」强制走确认链 + 锁屏密码闸，按 `android-control` 技能的设备维护章节操作。

## 参考

- `android-control` — 安卓设备安装/界面自动化/ADB 输入
