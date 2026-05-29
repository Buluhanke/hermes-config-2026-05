# 1688验证码深度分析

## 核心发现（2026-05-30 02:00）

### 1688使用阿里自研滑块验证码
- **非标准CAPTCHA**：1688的滑块验证是阿里巴巴自研的，非reCAPTCHA/hCaptcha/Turnstile等标准类型
- **NopeCHA不支持**：NopeCHA 2.0覆盖 reCAPTCHA v2/v3, hCaptcha, Cloudflare Turnstile, AWS WAF CAPTCHA 等标准类型，但**不包含1688阿里自研验证码**
- **影响**：采购自动化的"下单"环节被验证码阻断

### NopeCHA安装状态（2026-05-30验证）
```bash
# Hermes venv环境路径
/Users/aimac/.hermes/hermes-agent/venv/bin/python
# 安装命令
./venv/bin/pip install nopecha
# 验证成功
./venv/bin/python -c "import nopecha; print(nopecha.__version__)"  # 2.0.1
```

## 验证方案层级

### 第一层：NopeCHA（标准CAPTCHA）
- **覆盖**：reCAPTCHA, hCaptcha, Turnstile等
- **安装**：已安装（venv环境）
- **注册**：developers.nopecha.com（需API key）
- **适用场景**：非1688的平台标准验证码

### 第二层：1688自研滑块（待自研）
```python
# 思路框架（未实现）
1. 抓包识别1688验证码API
   - 1688验证码触发时，network请求中会有 wg-security.alibaba.com.cn 或 cf.1688.com 域名的请求
   
2. 分析滑块缺口位置算法
   - 滑块背景图 + 缺口图 = 需要滑动的距离
   - OpenCV 模板匹配计算缺口位置
   
3. 滑动轨迹模拟
   - Bezier曲线模拟人类滑动轨迹
   - 速度曲线：先快后慢，到缺口前减速
  
4. 如果自研失败
   - 人工回退：截图→发QQ→等待手动输入
```

### 第三层：人工回退（兜底）
- 遇到复杂验证码无法解决时
- 截图 → 发QQ给用户 → 等待手动输入验证码 → 继续自动化

## AI网站智囊关于1688验证码的问答记录

### 已在智囊验证的结论
1. AnySearch可用但不完美（数据粒度受限）
2. 1688直接URL访问100%触发验证码
3. CDP拦截仅在用户已登录时有效
4. 1688验证码是阿里自研滑动验证码

### 待验证（需要实际测试）
1. NopeCHA对1688验证码的实际效果（可能不支持）
2. 1688验证码自研的可行性（需要抓包逆向）
3. 1688商家确认是否可以通过其他渠道（电话/微信）替代旺旺联系

## 相关文件
- `../SKILL.md` — 主技能文档（包含AI网站智囊工作流）
- `1688-search-postmessage.md` — CDP拦截技术细节
- `ai-agents-1688-knowledge.md` — 智囊问答记录