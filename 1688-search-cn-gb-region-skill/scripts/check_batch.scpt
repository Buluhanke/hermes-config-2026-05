-- check_batch.scpt : 批量开详情页核对规格（模板，参数化 TARGET）
-- 用法：
--   1) 改 property TARGET 为本次目标尺寸（L*W*H，星号分隔），缺省 16*16*16
--   2) 把 IDS 列表换成本次 extract_offers.scpt 提取到的 offerId
--   3) 跑：osascript /path/check_batch.scpt
-- 结果写 outPath，每行 "id => {hit,joined,sq,target,title,prov,captcha,...}"
-- delay 8 防验证码；如返回 captcha:true 需真人过验证后降速重跑
property TARGET : "17.5*17.5*8.5"   -- ← 本次目标尺寸
property outPath : "/tmp/check_175.txt"

set myPath to POSIX path of (path to me)
set SKILL to do shell script "dirname " & quoted form of myPath & " | xargs dirname"
set jsRead to read (POSIX file (SKILL & "/scripts/check_spec.js")) as «class utf8»
set f to open for access POSIX file outPath with write permission
set eof of f to 0
tell application "Google Chrome"
  repeat with id in {"634522031289", "751990874462", "765857194469", "634987797003", "708938768516"}
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
return "done"
