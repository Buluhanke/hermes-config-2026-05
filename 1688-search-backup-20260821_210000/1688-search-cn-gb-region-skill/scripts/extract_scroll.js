(() => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  return (async () => {
    let prev = 0;
    for (let i = 0; i < 8; i++) {
      window.scrollTo(0, document.body.scrollHeight);
      await sleep(1500);
      const cur = document.querySelectorAll('a[href*="offer/"], a[href*="offerId"]').length;
      if (cur === prev && i > 2) break;
      prev = cur;
    }
    const html = document.documentElement.outerHTML;
    const ids = new Set();
    [...html.matchAll(/detail\.1688\.com\/offer\/(\d+)/g)].forEach(m => ids.add(m[1]));
    [...html.matchAll(/offerId["']?\s*[:=]\s*["']?(\d+)/g)].forEach(m => ids.add(m[1]));
    return JSON.stringify({count: ids.size, ids: [...ids].filter(id => id.length >= 9 && id.length <= 14)});
  })();
})();
