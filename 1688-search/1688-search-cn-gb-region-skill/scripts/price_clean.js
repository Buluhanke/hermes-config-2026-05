// price_clean.js : 提取阶梯价/起批量，中文转 \\uXXXX ASCII 安全回传
(() => {
  const esc = s => (s || '').replace(/[^\x00-\x7F]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
  const title = (((document.querySelector('h1') || {}).innerText) || document.title || '').trim().slice(0, 40);
  const txt = document.body.innerText || '';
  const lines = txt.split('\n').map(s => s.trim()).filter(Boolean);

  // 主价格
  let mainPrice = '';
  const pm = txt.match(/[¥￥]\s*([\d.]+)/);
  if (pm) mainPrice = '¥' + pm[1];

  // 起批量 / 最小起订
  let moq = '';
  const moqM = txt.match(/(起批量|最小起订量|起订量)[^\d]*(\d+)/);
  if (moqM) moq = moqM[2];

  // 阶梯价表：抓含 "件/个/只" + 价格的行
  const ladder = [];
  for (const l of lines) {
    const m = l.match(/([\d,]+(?:\+)?\s*(?:件|个|只|套|PCS|pcs)?\s*(?:[-~至到]\s*[\d,]+)?)\D*([¥￥]?\s*[\d.]+)\s*元?/i);
    if (m && /[\d.]/.test(l) && /(件|个|只|套|¥|￥|\d\.\d)/.test(l)) {
      ladder.push(l);
    }
  }

  // 抓报价区域关键词上下文
  const idx = lines.findIndex(l => /(阶梯价|拿样价|批量价|价格说明|报价)/.test(l));
  const quoteCtx = idx >= 0 ? lines.slice(idx, idx + 8) : [];

  return esc(JSON.stringify({
    title: title,
    mainPrice: mainPrice,
    moq: moq,
    ladder: ladder.slice(0, 10),
    quoteCtx: quoteCtx
  }));
})();
