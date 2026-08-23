// price_table.js : 抓详情页阶梯价表（sku报价表格），输出结构化的 [[起批量, 单价], ...]
(() => {
  const title = (((document.querySelector('h1') || {}).innerText) || document.title || '').trim().slice(0, 36);
  const root = document.querySelector('table, [class*="sku-table"], [class*="price-table"], [class*="offer-table"]');
  let rows = [];
  if (root) {
    root.querySelectorAll('tr').forEach(tr => {
      const cells = [...tr.querySelectorAll('td, th')].map(c => c.innerText.replace(/\s+/g, ' ').trim());
      if (cells.length) rows.push(cells);
    });
  }
  // 兜底：抓所有含 '起批量' / '件' / 价格的行文本
  const txt = document.body.innerText || '';
  const lines = txt.split('\n').map(s => s.trim()).filter(Boolean);
  const priceLines = lines.filter(l => /(起批量|≥|个|件|只|套|¥|￥|\d+\.\d+)/.test(l)).slice(0, 20);
  return JSON.stringify({ title: title, tableRows: rows.slice(0, 12), priceLines: priceLines });
})();
