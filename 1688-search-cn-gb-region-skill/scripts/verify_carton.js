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
  // mm 形式支持（1688 纸箱厂大量用 mm 标注：80×80×90mm = 8×8×9cm）
  // 仅当单维 ≤ 200（即 ≤200mm≈20cm，排除 800mm 大箱被误除成 80cm）才折算
  const dn = x => norm(parseFloat(x).toString());
  const srMM = /([0-9][0-9.]*)[ ]*[*×xX][ ]*([0-9][0-9.]*)[ ]*[*×xX][ ]*([0-9][0-9.]*)[ ]*mm/g;
  while ((m = srMM.exec(skuTxt)) !== null) {
    const a = parseFloat(m[1]), b = parseFloat(m[2]), c = parseFloat(m[3]);
    if (a <= 200 && b <= 200 && c <= 200) sizes.add(dn(a) + '*' + dn(b) + '*' + dn(c));
  }
  if (L === W) {
    const sqRe = new RegExp(escR(L) + SEP + escR(W) + '[^¥]{0,30}?' + escR(H) + '[ ]*(cm|CM|mm)?[ ]*[(]?[ ]*(高|厚)', 'i');
    if (sqRe.test(skuTxt)) sizes.add(L + '*' + W + '*' + H);
  }
  const connectedHit = sizes.has(targetNorm);
  const targetLW = norm(L + '*' + W);
  const targetH = norm(H);

  // ---- 矩阵式尺寸识别（verify_carton_matrix.js 合并）----
  // 场景：部分商品把尺寸拆成两个 SKU 轴：长宽轴（如 8x8（长宽））+ 高轴（如 9cm（高））
  // 组合后才形成 L*W*H。原连写+SQ拆写会漏掉这种（坑8 矩阵变体）。
  // 复用已有的 txt 变量（文件开头已声明：const txt = (document.body.innerText || '').replace(/[ ]+/g, ' ');）
  const lwRe = /([0-9][0-9.]*)[ ]*[xX×*][ ]*([0-9][0-9.]*)[ ]*[（(]?长宽/g;
  const lwSet = new Set();
  while ((m = lwRe.exec(txt)) !== null) lwSet.add(norm(m[1] + '*' + m[2]));
  const hRe = /([0-9][0-9.]*)[ ]*(cm|CM)?[ ]*[（）()]*[ ]*高/g;
  const hSet = new Set();
  while ((m = hRe.exec(txt)) !== null) hSet.add(norm(m[1]));
  const combRe = /([0-9][0-9.]*)[ ]*[xX×*][ ]*([0-9][0-9.]*)[ ]*[（(]?长宽[ )]*[;:]?[ ]*([0-9][0-9.]*)[ ]*(cm|CM)?[ ]*[）)]?[ ]*高/g;
  let combHit = false;
  while ((m = combRe.exec(txt)) !== null) {
    if (norm(m[1] + '*' + m[2]) === targetLW && norm(m[3]) === targetH) combHit = true;
  }
  const matrixHit = combHit || (lwSet.has(targetLW) && hSet.has(targetH));
  const skuHit = connectedHit || matrixHit;
  const cartonSig = /纸箱|瓦楞|快递箱|邮政箱|飞机盒|牛皮纸盒|搬家箱|收纳箱|包装盒|纸盒/.test(title + txt.slice(0, 2000));
  const giftSig = /礼盒|礼品盒|礼品包装|开窗|烫金|巧克力|糖果|食品|蛋糕|首饰|珠宝|化妆品|护肤品|伴手礼/.test(title);
  const isCarton = skuHit && cartonSig && !giftSig;
  // —— 所在地（江浙沪校验）：从详情页头部/店铺信息提取省份+城市 ——
  const provRe = /(江苏|浙江|上海|广东|福建|山东|河南|河北|北京|天津|安徽|江西|湖北|湖南|四川|重庆|辽宁|吉林|黑龙江|陕西|山西|广西|云南|贵州|甘肃|海南|内蒙古|宁夏|青海|新疆|西藏)/g;
  const locBlob = (txt.match(/(发货地|所在地|地址|公司地址|工厂地址)[：: ]*([\u4e00-\u9fa5]{2,10})/g) || []).join(' ');
  const provs = [...new Set((txt.match(provRe) || []))];
  const cityM = txt.match(/(江苏|浙江|上海|广东|福建|山东|河南|河北|北京|天津|安徽|江西|湖北|湖南|四川|重庆|辽宁|吉林|黑龙江|陕西|山西|广西|云南|贵州|甘肃|海南|内蒙古|宁夏|青海|新疆|西藏)([\u4e00-\u9fa5]{2,4}(市|区|县|镇|街道)?)/);
  const location = cityM ? (cityM[1] + (cityM[2] || '')) : (provs.join('') || '');
  const esc = s => (s == null ? '' : String(s)).replace(/[^\x00-\x7f]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
  return esc(JSON.stringify({ title: title.slice(0, 36), target: T, skuHit: skuHit, skuSizes: [...sizes].slice(0, 40), cartonSig: cartonSig, giftSig: giftSig, isCarton: isCarton, location: location, provinces: provs }));
})();
