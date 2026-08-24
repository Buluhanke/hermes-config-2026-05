// drive_playwright.js : 1688 江浙沪找品主驱动（Playwright 版，比裸 CDP/AppleScript 好维护）
//
// 设计要点（来自 2026-08-21 实战踩坑）：
//  1. 用 chromium.connectOverCDP('http://127.0.0.1:9222') 驱动【真实登录态 Chrome】
//     —— 不走 headless 直连：headless 无头指纹会被 1688 搜页「驗證碼攔截」风控；
//        连真实登录态的 CDP Chrome 则正常（真人路径）。
//  2. 搜页前必须先开 www.1688.com 首页【暖场建会话】，同 tab 再跳搜索，
//     否则端点级风控会踢回 login.taobao.com / 验证码页（cold-navigate 必挂）。
//  3. 提取用组合正则（detail.1688.com/offer/<id> 桌面路径 + 内联 JSON 里的 offerId= 数值）覆盖链接结构变化。
//     注意：移动版 detail.m.1688.com / h5.m.1688.com 已于 2026 起被墙（返回 Forbidden / 页面不存在），
//     本 skill 只走桌面端点 s.1688.com/selloffer/offer_search.htm 与 detail.1688.com/offer/<id>.html，绝不导航到 m.1688.com。
//  4. 规格/品类/价格复用 skill 自带的 verify_carton.js + price_clean3.js（以真实 SKU 列表为权威），
//     二者返回 ASCII 安全 JSON（中文转 \uXXXX），直接 JSON.parse 即可。
//
// 2026-08-21 能力升级（相对初版）：
//  A. 【精确立方体双记号搜索】1688 搜 `*` 是模糊匹配（含某维度 16cm 全排进池），`x` 才是精确立方体。
//     驱动同时跑 `DIM`(如 16*16*16) 与 `DIM_X`(16x16x16) 两组搜索，合并去重 —— 命中精度质变。
//  B. 【CDP 健康自检】开头先探 9222；挂了不擅自拉起（遵守"手动拉起"约束），而是打印精确启动命令让你执行。
//  C. 【持久化已验商品库】把验证过的商品写入 <skill>/store/verified.json，
//     下次跑同 DIM 任务自动跳过已验 ID（仅补新出现的），并按价/库存排序输出。
//  D. 【自动渲染 markdown 报告】跑完把结果写成 <skill>/store/<DIM>_<PROV>_report.md，无需手动转。
//
// 用法：环境变量覆盖 —— DIM / CARTON / PROV / PAGES / STOP_HIT / KNOWN / CDP / OUT / STORE
//   DIM=16*16*16 CARTON=纸箱 PROV=江苏,浙江,上海 PAGES=5 node drive_playwright.js
//
// 前置：真实 Chrome 以 chrome-cdp-profile（Profile）并以 --remote-allow-origins=* 启动，
//      保持 CDP 9222 在线（见 SKILL.md 坑24）。
// 依赖：npm install playwright   （无需 iconv-lite —— GBK 编码复用 python3）

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const net = require('net');

const HERE = __dirname;                                   // <skill根>/scripts
const SKILL = path.dirname(HERE);
const STORE_DIR = path.join(SKILL, 'store');
fs.mkdirSync(STORE_DIR, { recursive: true });
const verifyJs = fs.readFileSync(path.join(HERE, 'verify_carton.js'), 'utf8');
const priceJs  = fs.readFileSync(path.join(HERE, 'price_clean3.js'), 'utf8');

// —— 任务参数（环境变量覆盖）——
const DIM    = process.env.DIM    || '16*16*16';
const CARTON = process.env.CARTON || '纸箱';
const PROV   = process.env.PROV   || '江苏,浙江,上海';
const PAGES  = parseInt(process.env.PAGES || '3', 10);
const STOP   = parseInt(process.env.STOP_HIT || '0', 10);   // 0 = 不限制，验全部
const KNOWN  = (process.env.KNOWN || '').split(',').filter(Boolean);
const TARGET = DIM;                                       // verify_carton / price_clean3 用 window.TARGET
const OUT    = process.env.OUT || path.join(STORE_DIR, `${DIM}_${PROV}_result.json`);
const CDP    = process.env.CDP || 'http://127.0.0.1:9222';
const GAP    = 3000;
const DIMX   = DIM.replace(/\*/g, 'x');                    // 精确立方体记号

// GBK 百分号编码（复用 python3，免装 iconv-lite）
function gbkEnc(kw){
  return execSync(`python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1].encode('gbk')))" ${JSON.stringify(kw)}`).toString().trim();
}
const provEnc = encodeURIComponent(PROV);
function buildBase(dimNotation){
  const kw = dimNotation + 'cm' + CARTON;
  return `https://s.1688.com/selloffer/offer_search.htm?keywords=${gbkEnc(kw)}&province=${provEnc}&beginPage=`;
}

// 组合提取：兼容旧/新 1688 链接结构
const EXTRACT = `
(()=>{
  const h=document.documentElement.outerHTML;
  const ids=new Set(); let m;
  const re1=/detail\\.1688\\.com\\/offer\\/(\\d+)/g;
  while((m=re1.exec(h))!==null) ids.add(m[1]);
  const re2=/[?&]offerId=(\\d+)/g;
  while((m=re2.exec(h))!==null) ids.add(m[1]);
  const re3=/offerId["']?\\s*[:=]\\s*["']?(\\d+)/g;
  while((m=re3.exec(h))!==null) ids.add(m[1]);
  const box=document.querySelector('input.search-input,input.box-input,input#jsk-search-input')||{};
  return JSON.stringify({title:document.title, boxVal:box.value||'', ids:[...ids].filter(id=>id.length>=9&&id.length<=14)});
})();
`;

const sleep = ms => new Promise(r => setTimeout(r, ms));
const dec = s => { try { return JSON.parse(s); } catch (e) { return {}; } };

// —— 能力 B：CDP 健康自检（不擅自拉起，挂了打印精确启动命令）——
function cdpAlive(){
  return new Promise(res => {
    const u = new URL(CDP);
    const s = net.connect({ host: u.hostname, port: parseInt(u.port, 10) }, () => { s.destroy(); res(true); });
    s.on('error', () => res(false));
    s.setTimeout(2000, () => { s.destroy(); res(false); });
  });
}
function printLaunchHint(){
  console.error('\n⚠️  CDP 9222 未在线。请手动拉起（不要交给本脚本自动拉起）：\n');
  console.error(`   nohup "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\`);
  console.error(`     --remote-debugging-port=9222 \\`);
  console.error(`     --user-data-dir=$HOME/chrome-cdp-profile \\`);
  console.error(`     --profile-directory="Profile" \\`);
  console.error(`     '--remote-allow-origins=*' >/tmp/chrome_cdp.log 2>&1 &\n`);
  console.error('   拉起后再重跑本脚本。\n');
}

// —— 能力 C：持久化已验商品库 ——
const STORE_FILE = path.join(STORE_DIR, 'verified.json');
function loadStore(){ try { return JSON.parse(fs.readFileSync(STORE_FILE, 'utf8')); } catch(e){ return {}; } }
function saveStore(s){ fs.writeFileSync(STORE_FILE, JSON.stringify(s, null, 2)); }

// —— 能力 D：渲染 markdown 报告 ——
function renderMd(query, allIds, hits){
  const rows = hits.map((h,i)=>`| ${i+1} | ${h.id} | ${h.title} | ${h.price} | ${h.stock} | ${h.moq}个 | ${h.url} |`).join('\n');
  return `# 1688 找品结果：${query}\n\n执行时间：${new Date().toISOString().slice(0,19).replace('T',' ')}\n方法：Playwright connectOverCDP + 真实登录态 Chrome + 双记号(*/x)精确搜索 + 首页暖场 + 组合提取 + verify/price.js 实时复核\n筛选：province=${PROV}（服务端江浙沪筛选）\n\n## 实跑验证结论（逐详情页核对真实在售 SKU 含 ${DIM}）\n\n| # | 商品ID | 店铺/地区 | 单价 | 库存 | 起批 | 链接 |\n|---|--------|----------|------|------|------|------|\n${rows}\n\n> 提取候选 ${allIds} 个，验证命中 ${hits.length} 个。\n`;
}

(async () => {
  if (!await cdpAlive()) { printLaunchHint(); process.exit(2); }
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();
  // 暖场：先开首页建会话，避免搜页端点风控/验证码（坑25）
  await page.goto('https://www.1688.com/', { waitUntil: 'domcontentloaded', timeout: 40000 });
  await sleep(6000);

  // —— 能力 A：双记号搜索，合并去重 ——
  const seen = new Set();
  const allIds = [];
  const notations = [...new Set([DIM, DIMX])];
  for (const note of notations) {
    const BASE = buildBase(note);
    for (let pg = 1; pg <= PAGES; pg++) {
      await page.goto(BASE + pg, { waitUntil: 'domcontentloaded', timeout: 40000 });
      await sleep(7000);
      for (let i = 0; i < 8; i++) { await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await sleep(1000); }
      const data = dec(await page.evaluate(EXTRACT).catch(() => '{}'));
      const ids = data.ids || [];
      for (const id of ids) { if (!seen.has(id)) { seen.add(id); allIds.push(id); } }
      console.log(`[${note} page ${pg}] +${ids.length} total ${allIds.length}`);
    }
  }
  for (const k of KNOWN) { if (!seen.has(k)) { seen.add(k); allIds.push(k); } }

  // 能力 C：跳过已验 ID（同 DIM 任务续跑只补新出现的）
  const store = loadStore();
  const verifiedForDim = store[DIM] || {};
  const toVerify = allIds.filter(id => !verifiedForDim[id]);
  console.log(`[extract] unique ${allIds.length} | 已验跳过 ${allIds.length - toVerify.length} | 待验 ${toVerify.length}`);

  const dp = await ctx.newPage();
  const hits = [];
  for (const oid of toVerify) {
    await dp.goto(`https://detail.1688.com/offer/${oid}.html`, { waitUntil: 'domcontentloaded', timeout: 40000 });
    await sleep(3000);
    await dp.evaluate(`window.TARGET='${TARGET}';`);
    await sleep(500);
    const v = dec(await dp.evaluate(verifyJs).catch(() => '{}'));
    const p = dec(await dp.evaluate(priceJs).catch(() => '{}'));
    verifiedForDim[oid] = { isCarton: !!v.isCarton, title: v.title, price: p.targetPrice, stock: p.targetStock, moq: p.moq, at: Date.now() };
    if (v.isCarton) {
      hits.push({ id: oid, title: v.title, price: p.targetPrice, stock: p.targetStock, moq: p.moq, url: `https://detail.1688.com/offer/${oid}.html` });
      console.log(`[HIT ${hits.length}] ${oid} | ${v.title} | ${p.targetPrice} | 库存 ${p.targetStock}`);
    } else {
      console.log(`[   ] ${oid} skuHit=${v.skuHit} carton=${v.cartonSig} gift=${v.giftSig}`);
    }
    if (STOP && hits.length >= STOP) break;
    await sleep(GAP);
  }
  // 汇总：本 DIM 历史已验命中（按价升序，给出完整可用清单）
  const allHits = Object.entries(verifiedForDim).filter(([,x]) => x.isCarton).map(([id,x]) => ({id, ...x}));
  const ranked = allHits.sort((a,b)=> (parseFloat((a.price||'¥0').replace(/[^\d.]/g,''))||0) - (parseFloat((b.price||'¥0').replace(/[^\d.]/g,''))||0));

  await page.close(); await dp.close(); await browser.close();

  store[DIM] = verifiedForDim;
  saveStore(store);
  const result = { query: `${DIM}cm ${CARTON}，${PROV}`, notations, unique_ids: allIds.length, new_hits: hits.length, all_verified_hits: ranked.length, hits: ranked };
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2));
  const md = renderMd(`${DIM}cm ${CARTON}，${PROV}`, allIds.length, ranked);
  const mdPath = path.join(STORE_DIR, `${DIM}_${PROV}_report.md`);
  fs.writeFileSync(mdPath, md);
  console.log(`[done] 本次新命中 ${hits.length} | 累计已验命中 ${ranked.length} -> ${OUT}`);
  console.log(`[report] ${mdPath}`);
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
