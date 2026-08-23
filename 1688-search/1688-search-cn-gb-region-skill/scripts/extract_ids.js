(() => {
  const html = document.documentElement.outerHTML;
  const ids = new Set();
  [...html.matchAll(/detail\.1688\.com\/offer\/(\d+)/g)].forEach(m => ids.add(m[1]));
  [...html.matchAll(/offerId["']?\s*[:=]\s*["']?(\d+)/g)].forEach(m => ids.add(m[1]));
  const box = document.querySelector('input.search-input, input.box-input, input#jsk-search-input') || {};
  const boxVal = box.value || '';
  return JSON.stringify({title: document.title, boxVal: boxVal, ids: [...ids].filter(id => id.length >= 9 && id.length <= 14)});
})();
