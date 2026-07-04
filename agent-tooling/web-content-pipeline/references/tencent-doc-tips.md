# 腾讯文档抓取小贴士

## 问题
腾讯文档（doc.weixin.qq.com）采用动态渲染，直接抓取HTML可能只能得到框架或加载提示，而实际内容需JS执行后注入。

## 一线方案
1. 使用 `fetch_url.py --upgrade-to-js`（内部走Trafilatura+Playwright）  
   例：`python3 ~/.hermes/scripts/fetch_url.py https://doc.weixin.qq.com/sheet/... --upgrade-to-js`
2. 若仍未得到完整数据，尝试添加等待时间或滚动到底部触发懒加载。

## 浏览器交互方案（当需要点击、筛选等操作时）
- 使用 `computer_use` 定位并点击“展开全部”或“加载更多”按钮（若存在）
- 或使用 `browser_navigate` + `browser_snapshot` 检查AX树是否包含目标文本
- 必要时结合 `browser_vision` 进行OCR辅助确认

## 常见坑
- 某些文档需登录或权限：此时只能得到登录页提示，需先在Cookie中注入有效会话（高级用法）
- 大型表格可能分页加载：需滚动或点击分页按钮后再抓取
- 导出为Excel/CSV的链接往往在页脚，可直接抓取该链接后下载文件

## 验证方法
- 对比抓取前后的文本长度：正常内容应有显著增加
- 检查是否出现预期的表头或关键字（如“采购单”、“金额”等）
- 使用 `browser_console` 检查页面是否报错（如网络403、JS错误）