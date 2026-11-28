#!/usr/bin/env python3
"""1688 源采 AI 找货 - 真人式端到端（稳定版）
走 cai.1688.com 结果页，等商品卡片渲染，从 React fiber 提取完整数据。
用法: python3 cai_find.py "46*26*10cm纸箱" [--json] [--limit 20] [--intention deep_search]
不需签名、不依赖网络请求时序，只要页面渲染出卡片就能取数——像真人看页面一样。
"""
import json, urllib.request, urllib.parse, websocket, time, argparse, re

BASE="http://127.0.0.1:9333"

def clean(s):
    return re.sub(r"<[^>]+>","",str(s or "")).strip() if s else ""

class CDP:
    def __init__(self,ws): self.ws=ws; self.mid=0
    def call(self,m,p=None):
        self.mid+=1;self.ws.send(json.dumps({"id":self.mid,"method":m,"params":p or {}}))
        while True:
            x=json.loads(self.ws.recv())
            if x.get("id")==self.mid: return x
def conn(u): return CDP(websocket.create_connection(u,timeout=180,suppress_origin=True))

# 页面内提取脚本：从每张卡片的 React fiber 链上找 offerId 等字段，DOM 补店铺/销量/回头率
EXTRACT = r"""(()=>{
try{
const cards=[...document.querySelectorAll('[class*=offerCardItemMainWrapper]')];
const rows=[];
for(const c of cards){
  let f=c[Object.keys(c).find(k=>k.startsWith('__reactFiber'))];
  let rec={offerId:'',title:'',price:'',company:'',sales:'',repurchase:''};
  for(let i=0;i<12&&f;i++){
    try{
      const p=f.memoizedProps;
      if(p){
        if(p.offerId&&!rec.offerId) rec.offerId=String(p.offerId);
        if(p.title&&!rec.title) rec.title=String(p.title);
        if(p.price&&!rec.price) rec.price=String(p.price);
        if(p.item&&typeof p.item==='object'){
          if(p.item.offerId&&!rec.offerId) rec.offerId=String(p.item.offerId);
          if(p.item.title&&!rec.title) rec.title=String(p.item.title);
          if(p.item.price&&!rec.price) rec.price=String(p.item.price);
          if(p.item.companyName&&!rec.company) rec.company=String(p.item.companyName);
        }
      }
    }catch(e){}
    f=f.return;
  }
  // DOM 兜底（class 名带 hash 后缀，用 includes 匹配）
  const q=(sel)=>{const e=[...c.querySelectorAll('*')].find(x=>(x.className||'').toString().includes(sel));return e?e.textContent.trim():'';};
  if(!rec.title) rec.title=q('offerCardItemTitleText');
  if(!rec.price){const pe=q('offerCardItemPriceWrapper');if(pe) rec.price=pe.replace(/[^\d.]/g,'');}
  if(!rec.company) rec.company=q('offerCardCompanyName');
  if(!rec.sales) rec.sales=q('offerCardItemGmvInfo');
  if(!rec.repurchase) rec.repurchase=q('offerCardItemRepurchaseInfo');
  rows.push(rec);
}
return JSON.stringify(rows);
}catch(e){return JSON.stringify([{ERR:String(e)}]);}
})()"""

def find(query, limit=20, intention="fast_search", wait_s=90):
    url="https://cai.1688.com/newOfferSearchResult?q="+urllib.parse.quote(query,safe="")+"&intention="+intention
    req=urllib.request.Request(BASE+"/json/new?"+urllib.parse.quote(url,safe=""),method="PUT")
    tab=json.load(urllib.request.urlopen(req,timeout=15))
    try:
        c=conn(tab["webSocketDebuggerUrl"])
        c.call("Runtime.enable");c.call("Page.enable")
        deadline=time.time()+wait_s
        last=0
        while time.time()<deadline:
            time.sleep(4)
            r=c.call("Runtime.evaluate",{"expression":"document.querySelectorAll('[class*=offerCardItemMainWrapper]').length","returnByValue":True})
            n=(r.get("result",{}).get("result",{}) or {}).get("value") or 0
            last=n
            if n>0:
                break
        if not last: return []
        r=c.call("Runtime.evaluate",{"expression":EXTRACT,"returnByValue":True})
        v=(r.get("result",{}).get("result",{}) or {}).get("value") or "[]"
        try: rows=json.loads(v)
        except: return []
        items=[]
        seen=set()
        for x in rows:
            oid=x.get("offerId","")
            if not oid or oid in seen: continue
            seen.add(oid)
            items.append({
                "offerId":oid,"price":x.get("price",""),
                "company":clean(x.get("company","")),"title":clean(x.get("title","")),
                "sales":clean(x.get("sales","")),"repurchase":clean(x.get("repurchase","")),
                "url":"https://detail.1688.com/offer/"+oid+".html",
            })
        return items[:limit]
    finally:
        try: urllib.request.urlopen(BASE+"/json/close/"+tab["id"],timeout=5)
        except: pass

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("query");ap.add_argument("--json",action="store_true")
    ap.add_argument("--limit",type=int,default=20)
    ap.add_argument("--intention",default="fast_search",choices=["fast_search","deep_search"])
    a=ap.parse_args()
    items=find(a.query,a.limit,a.intention)
    if a.json:
        print(json.dumps(items,ensure_ascii=False,indent=1))
    else:
        print(f"{'ID':<15} {'单价':<8} {'店铺':<22} {'标题'}")
        for it in items:
            print(f"{it['offerId']:<15} ¥{str(it['price']):<7} {it['company'][:20]:<22} {it['title'][:30]}")
        print(f"\n共 {len(items)} 条 | 链接: https://detail.1688.com/offer/<ID>.html")
