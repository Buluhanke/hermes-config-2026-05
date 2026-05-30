# 1688验证码深度分析（2026-05-30 夜间学习）

## 核心结论

**1688验证码是阿里自研壁垒**，不在任何主流CAPTCHA服务的支持范围内。

## NopeCHA评估

| 项目 | 结果 |
|------|------|
| 版本 | v2.0.1（hermes venv，import正常） |
| 免费额度 | Chrome扩展100次/天 |
| API | 需要付费（无免费额度） |
| 1688支持 | ❌ 不支持（阿里自研滑块） |
| 结论 | 搁置 |

## 1688验证码技术特征

- **类型**：阿里云滑动验证码（nc-1-n1z元素）
- **特征**：滑动轨迹检测，非标准reCAPTCHA/hCaptcha/Turnstile
- **触发**：搜索页直接拦截（未登录态），登录页也有滑块
- **绕过难度**：极高，阿里自研+后端验证

## 替代方案

| 方案 | 状态 | 说明 |
|------|------|------|
| NopeCHA | ❌ 不支持 | 标准CAPTCHA服务 |
| DrissionPage | ⚠️ 部分可用 | 约50%成功率，需监听网络 |
| ali_captcha | ⚠️ 待验证 | 第三方方案 |
| 自研 | ❌ 高成本 | 需要大量标注数据 |

## DrissionPage监听1688验证码

```python
# 正确用法
page = ChromiumPage()
page.get('https://1688.com')
# ... 执行搜索触发验证码 ...
# 监听拦截URL
page.listen.start()  # 开始监听
time.sleep(5)
page.listen.wait(count=5, timeout=10)  # 等待5个请求，超时10秒
# 从_caught队列读取
while page.listen._caught:
    req = page.listen._caught.popleft()
    url = req.request.url
    if 'x5secdata' in url:
        print(f"Captcha intercepted: {url}")
```

## 反检测现状

- Camofox（已运行）+ patchright + nodriver 已解决指纹问题
- 平台更关注"你是谁"（账号行为）而非"你怎么点"（指纹）