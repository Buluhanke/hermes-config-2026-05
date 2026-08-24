// check_spec.js : 1688 详情页规格核对（通用，参数化尺寸）
// 尺寸从 window.TARGET 读取（AppleScript 先 execute "window.TARGET='17.5*17.5*8.5';" 设置），缺省 16*16*16
// 覆盖 * × x X 混用 + cm/CM 大小写 + 连写/拆写双匹配 + CAPTCHA 检测
(() => {
  const t = document.body.innerText;
  const title = (document.querySelector('h1') || {}).innerText || document.title || '';
  if (/CAPTCHA Verification/i.test(title)) {
    return JSON.stringify({ hit: false, captcha: true, title: title, url: location.href });
  }
  const T = (window.TARGET && window.TARGET.length) ? window.TARGET : '16*16*16';
  const parts = T.split('*');
  const L = parts[0].trim();
  const W = parts[1] ? parts[1].trim() : L;
  const H = parts[2] ? parts[2].trim() : L;
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const SEP = '[\\s*×xX]';
  const joinedRe = new RegExp(esc(L) + SEP + esc(W) + SEP + esc(H) + '\\s*(cm|CM)?', 'i');
  let sq = false;
  if (L === W) {
    const sqRe = new RegExp(esc(H) + '\\s*(cm|CM)?\\s*\\(?(高|厚|高\\s*\\))');
    sq = new RegExp(esc(L) + SEP + esc(W)).test(t) && sqRe.test(t);
  }
  const hit = joinedRe.test(t) || sq;
  const sample = t.split('\n').filter(l => l.indexOf(L) >= 0).slice(0, 4);
  return JSON.stringify({ hit: hit, joined: joinedRe.test(t), sq: sq, target: T, title: title.slice(0, 40), prov: '', sample: sample });
})();
