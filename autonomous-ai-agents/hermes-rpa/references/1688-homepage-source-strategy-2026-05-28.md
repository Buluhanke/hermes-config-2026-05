# 1688 找品策略：首页精选货源 vs 搜索结果页

## 核心发现（2026-05-28 实测）

**1688 搜索结果页（s.1688.com）严重反爬** — 直接访问搜索URL会触发滑块验证，返回"请拖动滑块"。

**✅ 正确路径：1688首页精选货源入口**
1. 打开 `https://www.1688.com`
2. 在输入框输入关键词 → 回车搜索
3. 从首页"精选货源"区块提取供应商数据

**为什么有用**：首页精选货源是1688主动推荐的流量区块，不经过搜索结果反爬链路。

## ❌ 不要尝试的URL

```python
# 这些URL全部触发反爬验证
"https://s.1688.com/company/search.html?keyword=气泡袋"
"https://s.1688.com/company/company_search.htm?keywords=纸箱"
"https://search.1688.com/selloffer/offer_search.html"
# 所有直接在URL带关键词参数的方式
```

## 从首页精选货源提取数据

```javascript
// 在 browser_navigate + Page.loadEventFired 后执行
Runtime.evaluate 表达式：

(function(){
  var results = [];
  var seenTxt = new Set();
  document.querySelectorAll('[class*="card"], [class*="item"], .seb-quotaitem').forEach(function(el){
    var txt = el.innerText;
    if(txt.match(/气泡袋/) && !seenTxt.has(txt.substring(0,30))){
      seenTxt.add(txt.substring(0,30));
      var price = (txt.match(/¥[\d.]+/) || [])[0] || '';
      var sold = (txt.match(/已售[\d万+件包]+/) || [])[0] || '';
      var moq = (txt.match(/\d+件起批|起订量[^\n]+/) || [])[0] || '';
      var comp = (txt.match(/[^\n]{4,30}(?:公司|厂|商行|合作社)/) || [])[0] || '';
      results.push({price, sold, moq, comp, text: txt.substring(0,150)});
    }
  });
  return JSON.stringify(results.slice(0,20));
})()
```

## 详情页 offerId 提取

从商品卡片 href 提取 offerId：
```python
import re
r = send("Runtime.evaluate", {
    "expression": 'document.body.innerHTML.match(/"offerId":(\\d+)"/)?.[0]',
    "returnByValue": True
})
raw = r.get('result',{}).get('result',{}).get('value','')
offer_ids = re.findall(r'(\d{10,})', raw)
```

## 1688 价格格式（已验证）

| 页面位置 | 价格格式 | 提取方式 |
|---------|---------|---------|
| 搜索列表页 | ¥1.6 | 第一个 match |
| 详情页 | ¥1.6~¥3.6（阶梯价） | 只取第1个match作为起批价 |
| 已售数量 | 已售2.0万+个 | 正则 `已售[\d万+件包]+` |

## 供应商信息提取

```python
# 从innerText中提取供应商名称
company = (text.match(/[^\n]{4,30}(?:公司|厂|商行|合作社)/) || [])[0] || ''
location = (text.match(/浙江[^\n]{0,15}|江苏[^\n]{0,15}|上海[^\n]{0,15}|安徽[^\n]{0,15}/) || [])[0] || ''
```