# 1688 油猴脚本

## 搜索页自动翻页提取

```javascript
// ==UserScript==
// @name         1688列表自动采集
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  1688搜索结果自动翻页+数据提取
// @match        https://s.1688.com/company/sale_*.html
// @match        https://s.1688.com/company/search.htm*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_download
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    const MAX_PAGES = 10;   // 最多翻10页，可调
    const SCROLL_DELAY = 2500;  // 滚动后等待加载时间(ms)
    const OUTPUT_FORMAT = 'csv';  // csv | json

    function extractProducts() {
        const items = document.querySelectorAll('.offer-list .offer-item, .list-item');
        const products = [];
        items.forEach((item, idx) => {
            try {
                const titleEl = item.querySelector('.title a, .product-title a, .mod-detailTitle a');
                const priceEl = item.querySelector('.price, .mod-price');
                const salesEl = item.querySelector('.sale, .sales');
                const shopEl = item.querySelector('.company-name a, .shop-name a');
                const addrEl = item.querySelector('.address, .location');
                const link = titleEl?.href || '';
                const idMatch = link.match(/(\d{6,})\.html/);
                const id = idMatch ? idMatch[1] : `unknown_${idx}`;
                products.push({
                    id, title: titleEl?.textContent?.trim() || '',
                    price: priceEl?.textContent?.trim()?.replace(/\s+/g, ' ') || '',
                    sales: salesEl?.textContent?.trim()?.replace(/\s+/g, ' ') || '',
                    shop: shopEl?.textContent?.trim() || '',
                    address: addrEl?.textContent?.trim()?.replace(/\s+/g, ' ') || '',
                    link, detailUrl: `https://detail.1688.com/offer/${id}.html`
                });
            } catch(e) {}
        });
        return products;
    }

    function exportData(products) {
        if (OUTPUT_FORMAT === 'json') {
            GM_download(new Blob([JSON.stringify(products, null, 2)], {type: 'application/json'}), '1688_products.json');
        } else {
            const header = Object.keys(products[0] || {}).join(',');
            const rows = products.map(p => Object.values(p).map(v => `"${String(v).replace(/"/g, '""')}"`).join(','));
            GM_download(new Blob(["\uFEFF" + [header, ...rows].join('\n')], {type: 'text/csv;charset=utf-8'}), '1688_products.csv');
        }
    }

    function run() {
        let allProducts = GM_getValue('allProducts', []);
        const currentPage = GM_getValue('currentPage', 1);
        console.log(`[1688采集] 第${currentPage}页，提取 ${extractProducts().length} 条`);
        allProducts = [...allProducts, ...extractProducts()];
        GM_setValue('allProducts', allProducts);
        if (currentPage >= MAX_PAGES) { exportData(allProducts); return; }
        window.scrollTo(0, document.body.scrollHeight);
        setTimeout(() => {
            const nextBtn = document.querySelector('.page-next, .next-page, .fenye .next');
            if (nextBtn && !nextBtn.classList.contains('disabled')) {
                GM_setValue('currentPage', currentPage + 1);
                nextBtn.click();
                setTimeout(run, SCROLL_DELAY);
            } else { console.log(`采集完成，共${allProducts.length}条`); exportData(allProducts); }
        }, SCROLL_DELAY);
    }

    GM_setValue('allProducts', []);
    GM_setValue('currentPage', 1);
    setTimeout(run, 1000);
})();
```

## 详情页 JS 提取（browser_console 用）

```javascript
// 在1688详情页控制台执行
(function(){
    const title = document.querySelector('.title, h1')?.textContent?.trim() || '';
    const priceText = document.querySelector('.price')?.textContent?.trim() || '';
    const minOrder = document.querySelector('.min-order')?.textContent?.trim() || '';
    const address = document.querySelector('.address')?.textContent?.trim() || '';
    const shopName = document.querySelector('.shop-name')?.textContent?.trim() || '';
    const priceTable = document.querySelector('.price-quantity-table, table.price-table');
    let tieredPrices = [];
    if (priceTable) {
        tieredPrices = Array.from(priceTable.querySelectorAll('tr')).slice(1).map(row =>
            Array.from(row.querySelectorAll('td')).map(c => c.textContent.trim())
        );
    }
    return JSON.stringify({ title, priceText, minOrder, address, shopName, tieredPrices }, null, 2);
})()
```
