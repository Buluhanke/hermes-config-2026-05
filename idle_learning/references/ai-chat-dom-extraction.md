# AI对话内容提取：CDP Runtime.evaluate vs 截图（2026-06-02）

## 教训
去ChatGPT咨询后想保存回复，第一时间想到`browser_vision`截图+OCR——走弯路了。

## 正确方式：CDP Runtime.evaluate 直接提取DOM文本

```python
import websocket, json, urllib.request

with urllib.request.urlopen('http://127.0.0.1:9222/json/list') as f:
    tabs = json.loads(f.read())
tab_id = tabs[0]['id']

ws = websocket.create_connection(f"ws://127.0.0.1:9222/devtools/page/{tab_id}", timeout=15)
ws.send(json.dumps({"id":1,"method":"Runtime.enable"})); ws.recv()

ws.send(json.dumps({
    "id": 2, "method": "Runtime.evaluate", "params": {
        "expression": """
(function(){
    var items = document.querySelectorAll('[data-testid*="conversation"] article, .markdown-comment, [class*="assistant"]');
    var texts = [];
    items.forEach(function(el){
        if(el.innerText.trim()) texts.push(el.innerText.substring(0,3000));
    });
    return JSON.stringify(texts.slice(-6));
})()
""",
        "returnByValue": True
    }
}))
msg = json.loads(ws.recv())
val = msg.get('result',{}).get('result',{}).get('value','')
if val:
    for t in json.loads(val): print(t[:1500])
ws.close()
```

## 对比

| 指标 | CDP Runtime.evaluate | browser_vision截图 |
|------|--------------------|--------------------|
| Token消耗 | ~300-500 | ~8000-100000 |
| 速度 | <1秒 | 3-8秒 |
| 准确性 | 100%（文本） | 95%（OCR误差） |

## 判断标准

- **AI网站对话内容**（ChatGPT、豆包、智谱清言）→ CDP Runtime.evaluate
- **动态渲染页面**（React/Vue SPA）→ CDP Runtime.evaluate
- **验证码/CAPTCHA/Canvas** → browser_vision 截图
- **表单/列表/普通网站** → dom_tag_and_extract