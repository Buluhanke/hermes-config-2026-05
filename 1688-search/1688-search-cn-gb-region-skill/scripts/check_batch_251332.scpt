-- check_batch_251332.scpt : 验证 84 个候选是否含 25*13*32（矩阵+连写）
property TARGET : "25*13*32"
property outPath : "/tmp/251332_check.txt"
property idFile : "/tmp/251332_ids.txt"

set jsRead to read (POSIX file "/Users/aimac/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts/verify_carton_matrix.js") as «class utf8»

-- 从文件读 ID 列表
set idText to read (POSIX file idFile) as «class utf8»
set idList to {}
repeat with ln in paragraphs of idText
  set t to trimmed(ln)
  if t is not "" and t is not missing value then
    if t contains onlyDigits(t) then set end of idList to t
  end if
end repeat

set f to open for access POSIX file outPath with write permission
set eof of f to 0
tell application "Google Chrome"
  repeat with id in idList
    set URL of active tab of front window to ("https://detail.1688.com/offer/" & id & ".html")
    delay 8
    try
      execute active tab of front window javascript ("window.TARGET='" & TARGET & "';")
      set r to execute active tab of front window javascript jsRead
      write (id & " => " & r & linefeed) to f
    on error errMsg
      write (id & " => ERR:" & errMsg & linefeed) to f
    end try
  end repeat
end tell
close access f
return "done " & (count of idList) & " ids"

on trimmed(s)
  set s to s as string
  repeat while s begins with " "
    set s to text 2 thru -1 of s
  end repeat
  repeat while s ends with " "
    set s to text 1 thru -1 of s
  end repeat
  return s
end trimmed

on onlyDigits(s)
  if length of s is 0 then return false
  repeat with c in characters of s
    if c is not in {"0","1","2","3","4","5","6","7","8","9"} then return false
  end repeat
  return true
end onlyDigits
