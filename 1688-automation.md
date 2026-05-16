# 1688自动化技能

## 环境要求
- CDP浏览器（Chrome调试实例，端口9333）
- 1688已登录
- conda环境 omni（OmniParser）

## 环境准备
```bash
# Chrome CDP调试实例（通过launchd启动）
# launchd: com.aimac.hermes-chrome-debug
# 端口: 9333

# OmniParser环境
export PYTHONPATH=~/projects/omniparser
conda activate omni
```

## 核心工具
- `browser_navigate`: 1688页面导航
- `browser_snapshot`: 读页面结构
- `browser_click/browser_type`: 操作交互
- `browser_vision`: 视觉验证（验证码/复杂UI）
- OmniParser: 截图→结构化元素（图标+文字）

## 1688操作流程

### 登录状态维持
Chrome实例已持久化登录态（通过launchd + 独立profile）

### 搜索产品
1. navigate to https://s.1688.com/youzhan/market/...
2. 输入关键词搜索
3. 筛选江浙沪地区
4. 按销量排序

### 获取供应商信息
- 公司名：从页面元素读取
- 价格：从价格元素读取
- 销量/交期：从标签读取
- 防爬：控制请求频率，必要时人化延迟

## 常见问题
- 验证码 → 使用browser_vision识别，或等待人工
- 页面加载慢 → 增加等待或刷新重试
- 登录态丢失 → 检查CDP连接，重新登录

## SeeClick集成
checkpoint路径: ~/projects/SeeClick
用于GUI元素定位（可选，OmniParser优先）
