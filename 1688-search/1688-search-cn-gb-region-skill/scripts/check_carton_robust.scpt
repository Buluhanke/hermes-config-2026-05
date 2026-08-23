-- check_carton_robust.scpt : 详情页规格+品类复核 健壮版 (坑20 修复版)
-- 替代 check_batch*.scpt：所有逐条 IO 走 do shell script 追加，不用 AppleScript open for access（会 -39 且截断续跑）
-- 用法：改 property TARGET / IDFILE / OUTFILE / STOP_HIT 即可复用任意任务
property TARGET : "16*16*16"          -- 目标尺寸（不带 cm）
property IDFILE : "/tmp/1688_ids.txt"  -- 主列表抓出的 offerId（每行一个）
property OUTFILE : "/tmp/check_carton.txt"
property STOP_HIT : 6                  -- 命中多少个真纸箱即停
property BATCH : 3
property GAP : 8

set jsRead to read (POSIX file "/Users/aimac/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts/verify_carton.js") as «class utf8»

-- 读已验 ID（断点续跑，不重扫）
set doneSet to {}
if (do shell script "test -f " & quoted form of OUTFILE & " && echo 1 || echo 0") is "1" then
  set dlines to do shell script "cat " & quoted form of OUTFILE
  repeat with dl in (paragraphs of dlines)
    if dl contains "\"id\":" then
      set mid to do shell script "echo " & quoted form of dl & " | sed -E 's/.*\"id\":\"([0-9]+)\".*/\\1/'"
      set end of doneSet to mid
    end if
  end repeat
end if

set idTxt to do shell script "cat " & quoted form of IDFILE
set IDS to {}
repeat with l in (paragraphs of idTxt)
  if length of l > 0 and (doneSet does not contain l) then set end of IDS to l
end repeat

tell application "Google Chrome"
  -- 防 0 窗口
  if (count of windows) is 0 then make new window
  set active tab index of front window to 1
  repeat with i from 1 to (count of IDS) by BATCH
    repeat with j from i to (i + BATCH - 1)
      if j > (count of IDS) then exit repeat
      set oid to item j of IDS
      try
        set URL of active tab of front window to "https://detail.1688.com/offer/" & oid & ".html"
        delay 4
        execute active tab of front window javascript "window.TARGET='" & TARGET & "';"
        delay 0.5
        set r to execute active tab of front window javascript jsRead
        if r is missing value then set r to "{\"id\":\"" & oid & "\",\"isCarton\":false,\"err\":true}"
        set r to "{\"id\":\"" & oid & "\"," & (text 2 thru -2 of r) & "}"
        do shell script "printf '%s\\n' " & quoted form of r & " >> " & quoted form of OUTFILE
      on error errMsg
        do shell script "printf '{\"id\":\"" & oid & "\",\"isCarton\":false,\"err\":true,\"msg\":\"%s\"}\\n' " & quoted form of errMsg & " >> " & quoted form of OUTFILE
      end try
    end repeat
    set total to do shell script "grep -c '\"isCarton\":true' " & quoted form of OUTFILE & " || true"
    if (total as integer) ≥ STOP_HIT then
      do shell script "echo STOP_AT_" & total & " >> " & quoted form of OUTFILE
      return "done cartons=" & total
    end if
    if i + BATCH ≤ (count of IDS) then delay GAP
  end repeat
end tell
return "done scanned all"
