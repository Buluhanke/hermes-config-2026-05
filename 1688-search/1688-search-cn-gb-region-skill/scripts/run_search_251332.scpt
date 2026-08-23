-- run_search_251332.scpt : 25*13*32cm 牛皮纸袋 江浙沪（双词合并，固化手册路线1）
-- 复用 run_search.scpt 结构，加「牛皮纸袋」第二词（矩阵/袋类卖家池）

property DIM : "25*13*32"        -- 目标尺寸
property CARTON : "牛皮纸袋"       -- 搜索词品类
property PROV : "江苏,浙江,上海"  -- 省份筛选(江浙沪)
property PAGES : 3               -- 翻页数
property OUT : "/tmp/251332_run.txt"

on gbkEncode(kw)
  do shell script "python3 -c \"import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1].encode('gbk')))\" " & quoted form of kw
end gbkEncode

on utf8Encode(s)
  do shell script "python3 -c \"import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))\" " & quoted form of s
end utf8Encode

set kw1 to DIM & "cm" & CARTON
set kw1Enc to my gbkEncode(kw1)
set kw2 to CARTON
set kw2Enc to my gbkEncode(kw2)
set provEnc to my utf8Encode(PROV)

set BASE1 to "https://s.1688.com/selloffer/offer_search.htm?keywords=" & kw1Enc & "&province=" & provEnc & "&beginPage="
set BASE2 to "https://s.1688.com/selloffer/offer_search.htm?keywords=" & kw2Enc & "&province=" & provEnc & "&beginPage="

set jsExtract to read (POSIX file "/Users/aimac/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts/extract_ids.js") as «class utf8»

do shell script "rm -f " & quoted form of OUT

tell application "Google Chrome"
  if (count of windows) is 0 then make new window
  set active tab index of front window to 1
  -- 词① 尺寸词
  repeat with pg from 1 to PAGES
    set URL of active tab of front window to (BASE1 & (pg as string))
    delay 7
    repeat 8 times
      execute active tab of front window javascript "window.scrollTo(0, document.body.scrollHeight);"
      delay 1
    end repeat
    set r to execute active tab of front window javascript jsExtract
    if r is missing value then set r to "{\"ids\":[]}"
    do shell script "printf 'DIM_P%s:%s\\n' " & (pg as string) & " " & quoted form of r & " >> " & quoted form of OUT
    delay 1
  end repeat
  -- 词② 牛皮纸袋
  repeat with pg from 1 to PAGES
    set URL of active tab of front window to (BASE2 & (pg as string))
    delay 7
    repeat 8 times
      execute active tab of front window javascript "window.scrollTo(0, document.body.scrollHeight);"
      delay 1
    end repeat
    set r to execute active tab of front window javascript jsExtract
    if r is missing value then set r to "{\"ids\":[]}"
    do shell script "printf 'BAG_P%s:%s\\n' " & (pg as string) & " " & quoted form of r & " >> " & quoted form of OUT
    delay 1
  end repeat
end tell
return "DONE ids -> " & OUT
