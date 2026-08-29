#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针6：验证 scoped EXTRACT（只取 search-offer-wrapper 真实卡）能过滤推荐挂件。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP
qp = __import__("urllib.parse", fromlist=["quote"])

SCOPED = r"""(()=>{
  const ids=new Set();
  const containers=document.querySelectorAll('.search-offer-wrapper,.page-offerlist,.space-common-offerlist');
  const roots=containers.length?containers:[document.documentElement];
  for(const root of roots){
    const h=root.innerHTML;
    let m;
    const re1=/detail\\.1688\\.com\\/offer\\/([0-9]+)/g;
    while((m=re1.exec(h))!==null) ids.add(m[1]);
    const re2=/detail\\.m\\.1688\\.com\\/page\\/index\\.html\\?offerId=([0-9]+)/g;
    while((m=re2.exec(h))!==null) ids.add(m[1]);
    const re3=/[?&]offerId=([0-9]+)/g;
    while((m=re3.exec(h))!==null) ids.add(m[1]);
  }
  return JSON.stringify({ids:[...ids].filter(id=>id.length>=9&&id.length<=14)});
})();"""

for mode in ["pc","mobile"]:
    if mode=="pc":
        url=("https://s.1688.com/selloffer/offer_search.htm?keywords="+qp.quote("18*14*10cm纸盒".encode("gbk"))
             +"&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD&beginPage=1")
    else:
        url=("https://m.1688.com/offer_search.html?keywords="+qp.quote("18*14*10cm纸盒".encode("gbk"))
             +"&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD&page=1")
    c=CDP("http://127.0.0.1:9222")
    tid,sess=c.new_page(url)
    time.sleep(9)
    raw=c.evaluate(sess, SCOPED, await_promise=False) or "{}"
    data=raw if isinstance(raw, dict) else (json.loads(raw) if raw else {})
    ids=data.get("ids",[])
    # 粗验：这些ID的详情页title是否真含 纸/盒
    print(f"=== {mode} scoped 候选数: {len(ids)} unique {len(set(ids))} ===")
    print("  前6:", ids[:6])
    c.close_target(tid, sess)
print("DONE")
