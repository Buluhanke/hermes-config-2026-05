// price_clean2.js : 单行化 + 抓报价区块 + 手机号式价格正则，ASCII安全
(() => {
  const esc = s => (s == null ? '' : String(s)).replace(/[^\x00-\x7F]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
  const strip = s => (s || '').replace(/[\x00-\x1F\x7F]/g, ' ').replace(/\s+/g, ' ').trim();
  const title = strip(((document.querySelector('h1') || {}).innerText) || document.title || '').slice(0, 40);

  // 报价 / 阶梯价 区块：常见 class
  let block = '';
  const sel = '.offer-price, .price-block, [class*="price"], [class*="sku"], [class*="table"]';
  document.querySelectorAll(sel).forEach(el => {
    const t = strip(el.innerText);
    if (t && /(¥|￥|\d+\.\d+|起批量|件|个|阶梯)/.test(t) && t.length < 600) block += t + ' || ';
  });

  // 兜底：整页正文行
  const lines = (document.body.innerText || '').split('\n').map(strip).filter(Boolean);
  const priceLines = [];
  for (const l of lines) {
    if (l.length > 120) continue;
    // 含价格符号或 数字+元/件/个
    if (/[¥￥]/.test(l) || /\d+\.\d+\s*(元|\/|起)/.test(l) || /^\d+(\.\d+)?\s*(件|个|只|套|PCS)$/i.test(l)) {
      priceLines.push(l);
    }
  }

  // 起批量
  let moq = '';
  const moqM = document.body.innerText.match(/(起批量|最小起订量|起订量)[:：]?\s*(\d+)/);
  if (moqM) moq = moqM[2];

  return esc(JSON.stringify({
    title: title,
    moq: moq,
    block: strip(block).slice(0, 400),
    priceLines: priceLines.slice(0, 14)
  }));
})();
