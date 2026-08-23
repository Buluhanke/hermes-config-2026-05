// grab_251332.js : 在详情页抠 skuMapOriginal 里 25长*13侧*32高 的真实价格+库存
(() => {
  const h = document.documentElement.outerHTML;
  const m = h.match(/skuMapOriginal"\s*:\s*(\[.*?\}\s*\])/);
  if (!m) return JSON.stringify({ err: "no skuMapOriginal" });
  let arr;
  try { arr = JSON.parse(m[1].replace(/\\"/g, '"')); }
  catch (e) { return JSON.stringify({ err: e.message }); }
  const t = arr.filter(s => /25长\*13侧\*32高|25\*13\*32|25x13x32/i.test(s.specAttrs || s.spec || ""));
  return JSON.stringify({
    total: arr.length,
    hit: t.slice(0, 8).map(s => ({
      spec: s.specAttrs || s.spec,
      price: s.discountPrice,
      stock: s.canBookCount
    }))
  }, null, 0);
})();
