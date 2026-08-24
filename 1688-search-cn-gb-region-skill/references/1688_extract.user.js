// ==UserScript==
// @name         1688 搜索结果提取 (offerList JSON)
// @namespace    hermes-agent
// @version     1.0
// @description 在1688搜索页用GM_xmlhttpRequest跨域调h5api拿offerList JSON, 提取offerId/标题/店铺/省份, 输出到页面浮层
// @match       https://s.1688.com/selloffer/offer_search.htm*
// @grant       GM_xmlhttpRequest
// @grant       GM_setClipboard
// @run-at      document-idle
// ==/UserScript==

(function () {
  "use strict";

  const APP_KEY = "12574478";

  function md5(s) {
    // 简易md5 (浏览器内置)
    function rotateLeft(lValue, iShiftBits) { return (lValue << iShiftBits) | (lValue >>> (32 - iShiftBits)); }
    function addUnsigned(lX, lY) { var lX4, lY4, lX8, lY8, lResult; lX8 = (lX & 0x80000000); lY8 = (lY & 0x80000000); lX4 = (lX & 0x40000000); lY4 = (lY & 0x40000000); lResult = (lX & 0x3FFFFFFF) + (lY & 0x3FFFFFFF); if (lX4 & lY4) return (lResult ^ 0x80000000 ^ lX8 ^ lY8); if (lX4 | lY4) { if (lResult & 0x40000000) return (lResult ^ 0xC0000000 ^ lX8 ^ lY8); else return (lResult ^ 0x40000000 ^ lX8 ^ lY8); } else return (lResult ^ lX8 ^ lY8); }
    function F(x, y, z) { return (x & y) | ((~x) & z); }
    function G(x, y, z) { return (x & z) | (y & (~z)); }
    function H(x, y, z) { return (x ^ y ^ z); }
    function I(x, y, z) { return (y ^ (x | (~z))); }
    function FF(a, b, c, d, x, s, ac) { a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac)); return addUnsigned(rotateLeft(a, s), b); }
    function GG(a, b, c, d, x, s, ac) { a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac)); return addUnsigned(rotateLeft(a, s), b); }
    function HH(a, b, c, d, x, s, ac) { a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac)); return addUnsigned(rotateLeft(a, s), b); }
    function II(a, b, c, d, x, s, ac) { a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac)); return addUnsigned(rotateLeft(a, s), b); }
    function convertToWordArray(str) { var lWordCount = (((str.length + 8) >> 6) + 1) * 16; var lWordArray = Array(lWordCount - 1); var lBytePosition = 0, lByteCount = 0; while (lByteCount < str.length) { lWordCount = (str.charCodeAt(lByteCount) << 24) | (str.charCodeAt(lByteCount + 1) << 16) | (str.charCodeAt(lByteCount + 2) << 8) | str.charCodeAt(lByteCount + 3); lWordArray[lBytePosition++] = lWordCount; lByteCount += 4; } lWordArray[lBytePosition] = lByteCount << 3; lWordArray[lWordCount - 2] = 0; return lWordArray; }
    function wordToHex(lValue) { var wordToHexValue = "", wordToHexValueTemp = "", lByte, lCount; for (lCount = 0; lCount <= 3; lCount++) { lByte = (lValue >>> (lCount * 8)) & 255; wordToHexValueTemp = "0" + lByte.toString(16); wordToHexValue += wordToHexValueTemp.substr(wordToHexValueTemp.length - 2, 2); } return wordToHexValue; }
    var x = convertToWordArray(str); var a = 1732584193, b = 4023233417, c = 2562383102, d = 271733878; var k, AA, BB, CC, DD, S11 = 7, S12 = 12, S13 = 17, S14 = 22, S21 = 5, S22 = 9, S23 = 14, S24 = 20, S31 = 4, S32 = 11, S33 = 16, S34 = 23, S41 = 6, S42 = 10, S43 = 15, S44 = 21; for (k = 0; k < x.length; k += 16) { AA = a; BB = b; CC = c; DD = d; a = FF(a, b, c, d, x[k], S11, 3614090360); d = FF(d, a, b, c, x[k + 1], S12, 3905402710); c = FF(c, d, a, b, x[k + 2], S13, 606105719); b = FF(b, c, d, a, x[k + 3], S14, 3250441966); a = FF(a, b, c, d, x[k + 4], S11, 4118548399); d = FF(d, a, b, c, x[k + 5], S12, 1200080426); c = FF(c, d, a, b, x[k + 6], S13, 2821735955); b = FF(b, c, d, a, x[k + 7], S14, 4249261313); a = FF(a, b, c, d, x[k + 8], S11, 1770035416); d = FF(d, a, b, c, x[k + 9], S12, 2336552879); c = FF(c, d, a, b, x[k + 10], S13, 4294925233); b = FF(b, c, d, a, x[k + 11], S14, 2304563134); a = FF(a, b, c, d, x[k + 12], S11, 1804603682); d = FF(d, a, b, c, x[k + 13], S12, 4254626195); c = FF(c, d, a, b, x[k + 14], S13, 2792965006); b = FF(b, c, d, a, x[k + 15], S14, 1236535329); a = GG(a, b, c, d, x[k + 1], S21, 4129170786); d = GG(d, a, b, c, x[k + 6], S22, 3225465664); c = GG(c, d, a, b, x[k + 11], S23, 643717713); b = GG(b, c, d, a, x[k], S24, 3921069994); a = GG(a, b, c, d, x[k + 5], S21, 3593408605); d = GG(d, a, b, c, x[k + 10], S22, 38016083); c = GG(c, d, a, b, x[k + 15], S23, 3634488961); b = GG(b, c, d, a, x[k + 4], S24, 3889429448); a = GG(a, b, c, d, x[k + 9], S21, 568446438); d = GG(d, a, b, c, x[k + 14], S22, 3275163606); c = GG(c, d, a, b, x[k + 3], S23, 4107603335); b = GG(b, c, d, a, x[k + 8], S24, 1163531501); a = GG(a, b, c, d, x[k + 13], S21, 2850285829); d = GG(d, a, b, c, x[k + 2], S22, 4243563512); c = GG(c, d, a, b, x[k + 7], S23, 1735328473); b = GG(b, c, d, a, x[k + 12], S24, 2368359562); a = HH(a, b, c, d, x[k + 5], S31, 4294588738); d = HH(d, a, b, c, x[k + 8], S32, 2272392833); c = HH(c, d, a, b, x[k + 11], S33, 1839030562); b = HH(b, c, d, a, x[k + 14], S34, 4259657740); a = HH(a, b, c, d, x[k + 1], S31, 2763975236); d = HH(d, a, b, c, x[k + 4], S32, 1272893353); c = HH(c, d, a, b, x[k + 7], S33, 4139469664); b = HH(b, c, d, a, x[k + 10], S34, 3200236656); a = HH(a, b, c, d, x[k + 13], S31, 4214956722); d = HH(d, a, b, c, x[k], S32, 3736229023); c = HH(c, d, a, b, x[k + 3], S33, 2999351573); b = HH(b, c, d, a, x[k + 6], S34, 138884848); a = II(a, b, c, d, x[k], S41, 1126891415); d = II(d, a, b, c, x[k + 7], S42, 1051523); c = II(c, d, a, b, x[k + 14], S43, 2850285829); b = II(b, c, d, a, x[k + 5], S44, 4243563512); a = II(a, b, c, d, x[k + 12], S41, 1735328473); d = II(d, a, b, c, x[k + 3], S42, 2368359562); a = II(a, b, c, d, x[k + 2], S43, 3736229023); d = II(d, a, b, c, x[k + 9], S42, 3275163606); c = II(c, d, a, b, x[k + 6], S43, 4107603335); b = II(b, c, d, a, x[k + 13], S44, 1163531501); a = II(a, b, c, d, x[k + 4], S41, 2755266504); d = II(d, a, b, c, x[k + 11], S42, 3813738440); c = II(c, d, a, b, x[k + 2], S43, 2999351573); b = II(b, c, d, a, x[k + 9], S44, 138884848); a = addUnsigned(a, AA); b = addUnsigned(b, BB); c = addUnsigned(c, CC); d = addUnsigned(d, DD); }
    var temp = wordToHex(a) + wordToHex(b) + wordToHex(c) + wordToHex(d); return temp.toLowerCase();
  }

  function getToken() {
    var m = document.cookie.match(/_m_h5_tk=([^;]+)/);
    return m ? m[1].split("_")[0] : "";
  }

  function searchAPI(keyword, province, page, pageSize, cb) {
    var t = Date.now();
    var params = {
      keywords: keyword, beginPage: page, pageSize: pageSize,
      method: "getOfferList", verticalProductFlag: "pcmarket",
      searchScene: "pcOfferSearch", charset: "GBK"
    };
    if (province) params.province = province;
    var dataObj = { appId: "32517", params: JSON.stringify(params) };
    var data = JSON.stringify(dataObj);
    var token = getToken();
    var sign = md5(token + "&" + t + "&" + APP_KEY + "&" + data);
    var url = "https://h5api.m.1688.com/h5/mtop.relationrecommend.WirelessRecommend.recommend/2.0/"
      + "?jsv=2.5.1&appKey=" + APP_KEY + "&t=" + t + "&sign=" + sign
      + "&api=mtop.relationrecommend.WirelessRecommend.recommend&v=2.0&data=" + encodeURIComponent(data);
    GM_xmlhttpRequest({
      method: "GET", url: url, headers: { "Referer": "https://s.1688.com/" },
      onload: function (resp) {
        try { var json = JSON.parse(resp.responseText); cb(json); }
        catch (e) { cb({ error: e.message, raw: resp.responseText.slice(0, 200) }); }
      },
      onerror: function (e) { cb({ error: "network " + e }); }
    });
  }

  function showResult(json) {
    var box = document.getElementById("hermes_1688_box");
    if (!box) {
      box = document.createElement("div");
      box.id = "hermes_1688_box";
      box.style.cssText = "position:fixed;top:10px;right:10px;width:420px;max-height:80vh;overflow:auto;background:#fff;border:2px solid #f60;z-index:99999;padding:10px;font-size:12px;box-shadow:0 0 10px rgba(0,0,0,.3)";
      document.body.appendChild(box);
    }
    var ret = (json.ret || [])[0] || "";
    if (ret.indexOf("SUCCESS") === 0) {
      var list = ((json.data || {}).data || {}).offerList || [];
      var html = "<b>找到 " + list.length + " 条 (total:" + (((json.data || {}).data || {}).totalCount || "?") + ")</b><br>";
      list.forEach(function (o) {
        var id = o.id || o.offerId;
        var title = (o.subject || o.title || "").replace(/<[^>]+>/g, "");
        var prov = ((o.company || {}).province || "") + ((o.company || {}).city || "");
        var name = (o.company || {}).name || "";
        var price = ((o.priceInfo || {}).price || (o.tradePrice || {}).offerPrice || {}).valueString || (o.priceRange || "");
        html += '<div style="border-bottom:1px solid #eee;padding:3px 0">' +
          '<a href="https://detail.1688.com/offer/' + id + '.html" target="_blank">' + (title.slice(0, 30)) + '</a><br>' +
          'ID:' + id + ' | ' + prov + ' | ' + name.slice(0, 20) + ' | ¥' + price + '</div>';
      });
      box.innerHTML = html;
      var ids = list.map(function (o) { return o.id || o.offerId; }).join(",");
      GM_setClipboard(ids);
      box.innerHTML += "<br><i>offerIds已复制到剪贴板: " + ids.slice(0, 80) + "...</i>";
    } else {
      box.innerHTML = "<b style='color:red'>接口返回: " + ret + "</b><br>" + JSON.stringify(json).slice(0, 300);
    }
  }

  // 自动从当前URL取关键词和省份
  function run() {
    var url = new URL(location.href);
    var kw = url.searchParams.get("keywords") || "纸箱";
    // keywords是GBK编码的, 需要解码
    try { kw = decodeURIComponent(escape(kw)); } catch (e) {}
    var prov = "";
    var p = url.searchParams.get("province");
    if (p) { try { prov = decodeURIComponent(p); } catch (e) { prov = p; } }
    searchAPI(kw, prov, 1, 20, showResult);
  }

  // 浮层按钮
  var btn = document.createElement("button");
  btn.textContent = "Hermes提取(JSON)";
  btn.style.cssText = "position:fixed;bottom:10px;right:10px;z-index:99999;background:#f60;color:#fff;border:none;padding:8px 12px;cursor:pointer;font-size:13px";
  btn.onclick = run;
  document.body.appendChild(btn);

  // 自动跑一次
  setTimeout(run, 3000);
})();
