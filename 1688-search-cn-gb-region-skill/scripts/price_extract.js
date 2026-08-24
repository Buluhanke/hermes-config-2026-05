// price_extract.js : 1688 详情页 阶梯价 + 起批量 提取
(() => {
  const title = (((document.querySelector('h1') || {}).innerText) || document.title || '').trim().slice(0, 40);
  const txt = document.body.innerText || '';
  const lines = txt.split('\n').map(s => s.trim()).filter(Boolean);
  // 起批量/起订量 区块（阶梯价表）
  let idx = lines.findIndex(l => /起批量|起订量|最小起订|价格区间/.test(l));
  let moqBlock = idx >= 0 ? lines.slice(Math.max(0, idx - 1), idx + 9) : [];
  // 价格行（含 ¥ 或 元 或 区间）
  const priceLines = lines.filter(l => /(¥|￥|\d+\.\d+\s*元|-\d+\.\d+)/.test(l)).slice(0, 14);
  // 默认展示价
  const pEl = document.querySelector('.price, [class*="price"]');
  const defaultPrice = pEl ? pEl.innerText.replace(/\s+/g, ' ').trim().slice(0, 50) : '';
  return JSON.stringify({ title: title, defaultPrice: defaultPrice, moqBlock: moqBlock, priceLines: priceLines });
})();
