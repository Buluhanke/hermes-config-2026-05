-- extract_offers.scpt : 在已打开的 1688 搜索结果页提取主列表 offerId（解析内联 HTML，不扫 a.href）
-- 用法：osascript /path/extract_offers.scpt   （当前 active tab 须是 offer_search.htm 结果页）
-- 注意：JS 文件必须用 «class utf8» 读，否则中文/正则乱码
set jsExtract to "(() => {
  const html = document.documentElement.outerHTML;
  const ids = new Set();
  [...html.matchAll(/detail\\.1688\\.com\\/offer\\/(\\d+)/g)].forEach(m => ids.add(m[1]));
  [...html.matchAll(/offerId[\"']?\\s*[:=]\\s*[\"']?(\\d+)/g)].forEach(m => ids.add(m[1]));
  return JSON.stringify([...ids].filter(id => id.length >= 9 && id.length <= 14));
})();"
tell application "Google Chrome"
  set active tab index of front window to 1
  delay 1
  set r to execute active tab of front window javascript jsExtract
  return "IDS:" & r
end tell
