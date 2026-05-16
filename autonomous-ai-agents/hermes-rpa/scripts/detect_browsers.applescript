(*
  检测所有打开的浏览器窗口及其活跃标签页
  用途：Hermes 连接用户浏览器前，先探测有哪些窗口可用

  用法: osascript scripts/detect_browsers.applescript
*)

-- 第1步：检测哪些浏览器正在运行
tell application "System Events"
    set browserList to {}
    set allProcs to every process whose background only is false
    set browserNames to {"Google Chrome", "Safari", "Firefox", "Microsoft Edge", "Arc", "Brave Browser", "Opera", "Vivaldi"}
    repeat with proc in allProcs
        set pname to name of proc
        repeat with bname in browserNames
            if pname contains bname then
                set end of browserList to pname
                exit repeat
            end if
        end repeat
    end repeat
end tell

if browserList is {} then
    log "未检测到打开的浏览器"
    return
end if

log "检测到以下浏览器:"
repeat with b in browserList
    log "  " & b
end repeat

-- 第2步：对每个浏览器列出窗口和标签页
repeat with b in browserList
    try
        tell application b
            set winCount to count of windows
            if winCount = 0 then
                log b & ": 无窗口"
            else
                log b & ": " & winCount & " 个窗口"
                repeat with w from 1 to winCount
                    try
                        set tabCount to count of tabs of window w
                        set winTitle to title of window w
                        log "  窗口" & w & " (" & tabCount & " 标签): " & winTitle
                        -- 只显示前10个标签标题，避免太长
                        set maxTabs to tabCount
                        if maxTabs > 10 then set maxTabs to 10
                        repeat with t from 1 to maxTabs
                            try
                                set tabTitle to title of tab t of window w
                                set tabURL to URL of tab t of window w
                                if length of tabTitle > 60 then
                                    set tabTitle to text 1 thru 60 of tabTitle & "..."
                                end if
                                if length of tabURL > 80 then
                                    set tabURL to text 1 thru 80 of tabURL & "..."
                                end if
                                log "    [" & t & "] " & tabTitle
                                log "         " & tabURL
                            end try
                        end repeat
                        if tabCount > 10 then
                            log "    ... 还有 " & (tabCount - 10) & " 个标签未显示"
                        end if
                    end try
                end repeat
            end if
        end tell
    on error errMsg
        log b & ": 无法访问 - " & errMsg
    end try
end repeat
