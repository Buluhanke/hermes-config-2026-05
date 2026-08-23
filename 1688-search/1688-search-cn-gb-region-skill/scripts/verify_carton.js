// verify_carton.js : 复核是否真·纸箱 + 尺寸必须是真实在售 SKU（排除广告文案误杀/误中）
// 权威：规格命中来源 = 真实 SKU 尺寸集合（仅 .module-od-sku-selection 的 DOM 文本，绝不并内嵌 <script>）
// 品类：纸箱/包装盒信号（放宽到 包装盒|纸盒，避免只写"包装盒"的真纸箱被误杀，坑17 修正）
// 排除：礼盒/食品/化妆品等信号仍强排除
// 返回一律 ASCII 安全（esc 把中文转 uXXXX），避免 AppleScript 桥接中文乱码/返回非 JSON
// 注意：本文件刻意不用 \d \s \. 等反斜杠转义（write_file 会双写），改用 [0-9] [ ] [.] 等价写法
(() => {
  const title = (((document.querySelector('h1') || {}).innerText) || document.title || '').trim();
  const txt = (document.body.innerText || '');
  const T = (window.TARGET && window.TARGET.length) ? window.TARGET : '16*16*16';
  const parts = T.split('*');
  const L = parts[0].trim(), W = parts[1] ? parts[1].trim() : L, H = parts[2] ? parts[2].trim() : L;
  const escR = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const SEP = '[ ]*×xX';
  const norm = s => s.replace(/[.]0$/g, '').replace(/[ ]+/g, '');
  const targetNorm = norm(L + '*' + W + '*' + H);

  const skuEl = document.querySelector('.module-od-sku-selection');
  let skuTxt = skuEl ? (skuEl.innerText || '').replace(/[ ]+/g, ' ') : '';
  // 注意：不加内嵌 <script> productPackInfo 兜底——那些 script 含跨商品广告文案尺寸，
  // 会污染尺寸集合造成假阳性（16*16*16 实战 751990874462 即因此误中）。
  // .module-od-sku-selection 的 DOM 文本才是本商品真实在售 SKU，权威来源。

  const sizes = new Set();
  const sr = /([0-9][0-9.]*)[ ]*[*×xX][ ]*([0-9][0-9.]*)[ ]*[*×xX][ ]*([0-9][0-9.]*)[ ]*(cm|CM)?/g;
  let m;
  while ((m = sr.exec(skuTxt)) !== null) sizes.add(norm(m[1] + '*' + m[2] + '*' + m[3]));
  if (L === W) {
    const sqRe = new RegExp(escR(L) + SEP + escR(W) + '[^¥]{0,30}?' + escR(H) + '[ ]*(cm|CM)?[ ]*[(]?[ ]*(高|厚)', 'i');
    if (sqRe.test(skuTxt)) sizes.add(L + '*' + W + '*' + H);
  }
  const skuHit = sizes.has(targetNorm);
  const cartonSig = /纸箱|瓦楞|快递箱|邮政箱|飞机盒|牛皮纸盒|搬家箱|收纳箱|包装盒|纸盒/.test(title + txt.slice(0, 2000));
  const giftSig = /礼盒|礼品盒|礼品包装|开窗|烫金|巧克力|糖果|食品|蛋糕|首饰|珠宝|化妆品|护肤品|伴手礼/.test(title);
  const isCarton = skuHit && cartonSig && !giftSig;
  const esc = s => (s == null ? '' : String(s)).replace(/[^\x00-\x7f]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
  return esc(JSON.stringify({ title: title.slice(0, 36), target: T, skuHit: skuHit, skuSizes: [...sizes].slice(0, 40), cartonSig: cartonSig, giftSig: giftSig, isCarton: isCarton }));
})();
