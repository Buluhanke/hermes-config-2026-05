-- run_search.scpt : 1688 江浙沪找品主驱动（参数化，替所有 *_2020.scpt 写死副本）
--
-- 改这 4 个常量即可复用任意任务：
property DIM : "20*20*10"        -- 目标尺寸（不带 cm，脚本自动补）
property CARTON : "纸箱"          -- 搜索词品类后缀
property PROV : "江苏,浙江,上海"  -- 省份筛选
property PAGES : 5               -- 翻页数
property OUT : "/tmp/1688_run_result.txt"

-- 用 python 把整个关键词按 GBK 编码（坑2：1688 关键词必须 GBK，不能 UTF-8）
on gbkEncode(kw)
  do shell script "python3 -c \"import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1].encode('gbk')))\" " & quoted form of kw
end gbkEncode

-- 省份用 UTF-8 编码（province 参数服务端认 UTF-8）
on utf8Encode(s)
  do shell script "python3 -c \"import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))\" " & quoted form of s
end utf8Encode

set kw to DIM & "cm" & CARTON
set kwEnc to my gbkEncode(kw)
set provEnc to my utf8Encode(PROV)

set BASE to "https://s.1688.com/selloffer/offer_search.htm?keywords=" & kwEnc & "&province=" & provEnc & "&beginPage="

-- run_search.scpt : 1688 江浙沪找品主驱动（参数化）
-- 注意：路径全部相对化（用 path to me 推断 skill 根），不写死机器（坑24 分发铁律）
set myPath to POSIX path of (path to me)
set SKILL to do shell script "dirname " & quoted form of myPath & " | xargs dirname"
set jsExtract to read (POSIX file (SKILL & "/scripts/extract_ids.js")) as «class utf8»

-- 坑19b：文件 IO 一律走 shell，不碰 open for access
do shell script "rm -f " & quoted form of OUT

tell application "Google Chrome"
  -- 窗口守卫：无 front window 时新建（避免 -1719 不能获得 window 1）
  if (count of windows) is 0 then make new window
  set active tab index of front window to 1
  repeat with pg from 1 to PAGES
    set URL of active tab of front window to (BASE & (pg as string))
    delay 7
    -- 滚动懒加载（坑19：首屏只渲染少量，须滚 8 次）
    repeat 8 times
      execute active tab of front window javascript "window.scrollTo(0, document.body.scrollHeight);"
      delay 1
    end repeat
    set r to execute active tab of front window javascript jsExtract
    if r is missing value then set r to "{\"ids\":[]}"
    do shell script "printf 'PAGE%s:%s\\n' " & (pg as string) & " " & quoted form of r & " >> " & quoted form of OUT
    delay 1
  end repeat
end tell
return "DONE ids -> " & OUT
