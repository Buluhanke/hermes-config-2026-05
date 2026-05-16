# ISV 入驻注册 — 实地踩坑记录

## Session 1 (2026-05-10)

### 前置条件
- 用户已登录 1688（账号: yiwuxunlong，买家号）
- 1688 账号已绑定手机号（180****6283），身份已认证
- **但邮箱未绑定** — 这是"主站信息未填写"的原因

### 踩坑流程

#### 1. 打开开放平台
`browser_navigate("https://open.1688.com")` → 正常访问，右上角显示用户名 `yiwuxunlong`

#### 2. 点击"控制中心"
`browser_click(ref="e9")` → 跳转到注册页 `open.1688.com/support/register`
弹出 dialog：
> **"1688主站信息未填写"**
> 两个"此处"链接 + "我知道了"按钮

#### 3. 点击 dialog 中的"此处"链接
`browser_click(ref="e1")` → 跳转到 `member.1688.com/member/account_security`
看到：
- 会员名：yiwuxunlong
- 手机号码：180****6283（已绑定）
- 登录邮箱：暂无 ← **需要绑定**
- 身份认证：已认证

绑定邮箱 `idluoyuan@qq.com` 后继续。

#### 4. 入驻注册表字段（初始状态）
| 字段 | 状态 | 说明 |
|------|------|------|
| 你的角色 | 下游平台角色/专业买家 | 默认，无法修改 |
| 登录账号 | yiwuxunlong | 自动 |
| 电子邮箱 | 空 | 需绑定后自动填入 |
| 手机号 | 空 | 需输入 |
| 短信验证码 | 空 | 点"获取验证码"收短信 |
| 支付宝账号 | 禁用 | 必须点"绑定企业支付宝" |
| 入驻原因 | 空 | 必填 |
| 联系人钉钉 | 空 | 可选 |
| 营业执照 | 空 | 需上传原件照片（≤2M） |
| 同意协议 | 未勾选 | 必须勾选 |

#### 5. 卡住原因（blocker）
- 用户是纯买家账号（无1688店铺），没有企业支付宝
- 入驻需要企业支付宝绑定 + 营业执照上传
- 纯买家账号无法注册为 ISV 开发者

### 结论
**纯买家账号无法通过 ISV 入驻注册。** 如果用户确实想用 1688 Open Platform API，需要：
1. 注册企业支付宝
2. 拥有营业执照
3. 在 1688 开通卖家身份

对于纯采购场景（找品、下单），CDP 浏览器自动化是更可行的方案。

---

## Session 2 (2026-05-10 v2 — 用户已备齐资质)

### 前置条件变更
- 用户已绑定企业支付宝（`249664130@qq.com`，义乌市迅龙贸易有限公司）
- 用户已拥有营业执照原件照片
- 邮箱已绑定（`idluoyuan@qq.com`）
- 1688 登录态通过 CDP 持久化 Chrome 保持

### 重新入驻流程

#### 1. 导航到入驻页
`browser_navigate("https://open.1688.com/support/register")` → 显示欢迎页和身份选择

#### 2. 点击"立即入驻"
`browser_click(ref=e61)` → 展开入驻表单

#### 3. 表单状态（第二次进入）
| 字段 | 当前值 | 操作 |
|------|--------|------|
| 你的角色 | **LP合作渠道商** | 自动（与 Session 1 不同！账号类型变化导致） |
| 登录账号 | yiwuxunlong | 自动 |
| 电子邮箱 | **空** | 需要手动填写或等同步 |
| 手机号 | **空** | 需要手动填写 |
| 短信验证码 | textbox ref=e54 | 点"获取验证码"按钮 ref=e53 → 输入 |
| 支付宝账号 | **249664130@qq.com** | 已绑定（disabled），无需操作 |
| 支付宝类型 | **企业支付宝** | 已绑定（disabled） |
| 支付宝实名 | **义乌市迅龙贸易有限公司** | 已绑定（disabled），但有"重新绑定"按钮 ref=e58 |
| 入驻原因 | textbox ref=e59 | 需填写文字原因 |
| 联系人钉钉 | textbox ref=e64 | 可选 |
| 营业执照 | button "plus 上传图片" ref=e61 | **需上传** |
| 同意协议 | checkbox ref=e65 | 需勾选 |
| 申请入驻 | button ref=e51 | 最终提交 |

#### 4. CDP 文件上传方法
营业执照的上传按钮 (ref=e61) 是一个 `<button>`，点击后 JS 打开隐藏的 `<input type="file">`。上传步骤：
1. `browser_click(ref=e61)` 点击上传按钮
2. 在浏览器 console 查找隐藏 input：
   ```javascript
   document.querySelector('input[type="file"]')
   // → <input type="file" accept="image/jpeg, image/jpg, image/bmp, image/png, image/gif" style="display: none;">
   ```
3. 需要用户提供文件的**绝对路径**（如 `/Users/aimac/Desktop/营业执照.jpg`）
4. 通过 CDP `DOM.setFileInputFiles` 或 Playwright file chooser 设置文件

#### 5. 剩余待办项
- [ ] 用户提供营业执照文件路径 → 上传
- [ ] 填写电子邮箱
- [ ] 填写手机号
- [ ] 获取并输入短信验证码
- [ ] 填写入驻原因
- [ ] 勾选同意协议
- [ ] 点击"申请入驻"
- [ ] 等待审核（1-3个工作日）
- [ ] 审核通过 → 控制中心 → 创建应用 → AppKey/AppSecret

### 关键差异点（Session 1 vs Session 2）
| 项目 | Session 1 | Session 2 |
|------|-----------|-----------|
| 角色 | 下游平台角色/专业买家 | LP合作渠道商 |
| 支付宝 | 未绑定（blocker） | ✅ 已绑定企业支付宝 |
| 邮箱 | 未绑定（blocker） | ✅ 已绑定 idluoyuan@qq.com |
| CDP | 调试中 | ✅ 9333 端口 stable |
| 营业执照 | 无 | 用户已有实体执照照片 |
| 进度 | blocked | 继续推进中 |
