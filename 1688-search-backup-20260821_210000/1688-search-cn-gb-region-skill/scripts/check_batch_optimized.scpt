-- check_batch_optimized.scpt : 降速+单批+命中即停 (方案0优化版)
-- 改 property TARGET 设目标尺寸; 改 IDS 列表; 单批3个, 间隔8s, 命中>=5即停
property TARGET : "17.5*17.5*8.5"
property MAX_OPEN : 6
property BATCH : 3
property GAP : 8
property STOP_HIT : 5

set jsRead to read (POSIX file "/Users/aimac/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts/check_spec.js") as «class utf8»
set outPath to "/tmp/check_175_opt.txt"

-- 断点续跑：读已验 ID（坑19b：文件 IO 一律走 shell，不碰 open for access）
set doneSet to {}
if (do shell script "test -f " & quoted form of outPath & " && echo 1 || echo 0") is "1" then
  set dlines to do shell script "cat " & quoted form of outPath
  repeat with dl in (paragraphs of dlines)
    if dl contains "\"id\":" then
      set mid to do shell script "echo " & quoted form of dl & " | sed -E 's/.*\"id\":\"([0-9]+)\".*/\\1/'"
      set end of doneSet to mid
    end if
  end repeat
end if

set IDS to {"642657577198", "680290011362", "520780210513", "642488458376", "651068843427", "1001004056388"}
set IDS to {}
repeat with cand in {"642657577198", "680290011362", "520780210513", "642488458376", "651068843427", "1001004056388"}
  if doneSet does not contain cand then set end of IDS to cand
end repeat

tell application "Google Chrome"
  -- 窗口守卫：无 front window 时新建（避免 -1719）
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
        if r is missing value then set r to "{\"id\":\"" & oid & "\",\"hit\":false,\"title\":\"ERROR\"}"
        set r to "{\"id\":\"" & oid & "\"," & (text 2 thru -2 of r) & "}"
        do shell script "printf '%s\\n' " & quoted form of r & " >> " & quoted form of outPath
      on error errMsg
        do shell script "printf '{\"id\":\"" & oid & "\",\"hit\":false,\"err\":true,\"msg\":\"%s\"}\\n' " & quoted form of errMsg & " >> " & quoted form of outPath
      end try
    end repeat
    set total to do shell script "grep -c '\"hit\":true' " & quoted form of outPath & " || true"
    if (total as integer) ≥ STOP_HIT then exit repeat
    if i + BATCH ≤ (count of IDS) then delay GAP
  end repeat
end tell
return "done optim"
