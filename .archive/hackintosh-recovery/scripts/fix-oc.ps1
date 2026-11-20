# fix-oc.ps1 -- 回滚黑苹果 OpenCore「修键盘」改动（在 Windows 上运行）
$ErrorActionPreference = 'Stop'
function Banner($t){ Write-Host "`n==== $t ====" -ForegroundColor Cyan }
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]'Administrator')) {
    Write-Host '请右键「以管理员身份运行」PowerShell 后再粘贴本脚本！' -ForegroundColor Red; exit 1
}

Banner '1) 定位 EFI 系统分区'
$efi = Get-Partition | Where-Object {
    ($_.Type -eq 'System') -or ($_.GptType -eq 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B')
} | Where-Object { [string]::IsNullOrEmpty($_.DriveLetter) } | Select-Object -First 1

$letter = $null
if ($efi) {
    foreach ($c in @('Z','Y','X','W','V')) {
        try { $efi | Set-Partition -NewDriveLetter $c -ErrorAction Stop; $letter = $c; break } catch {}
    }
}
if (-not $letter) { foreach ($c in @('Z','Y','X','W','V')) { if (Test-Path "${c}:\EFI") { $letter = $c; break } } }
if (-not $letter) { Write-Host '找不到 EFI 分区。确认黑苹果系统盘已连到这台 Windows。' -ForegroundColor Red; exit 1 }
Write-Host "EFI 盘符: $letter`:  (磁盘 $($efi.DiskNumber) 分区 $($efi.PartitionNumber))"

$efiRoot = "${letter}:\EFI"
$ocCfg = Join-Path $efiRoot 'OC\config.plist'
$cloverCfg = Join-Path $efiRoot 'CLOVER\config.plist'
$cfgPath = if (Test-Path $ocCfg) { $ocCfg } elseif (Test-Path $cloverCfg) { $cloverCfg } else {
    Write-Host '该 EFI 里没有 OC/CLOVER 的 config.plist。' -ForegroundColor Red; exit 1
}
Write-Host "配置文件: $cfgPath"

Banner '2) 备份'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDir = Join-Path ([Environment]::GetFolderPath('Desktop')) "OC-FIX-BACKUP-$stamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item $cfgPath (Join-Path $backupDir 'config-backup.plist') -Force
try { Compress-Archive -Path $efiRoot -DestinationPath (Join-Path $backupDir 'EFI-full.zip') -Force } catch { Write-Host '(EFI 压缩跳过，已有 config 备份)' -ForegroundColor Yellow }
Write-Host "备份: $backupDir"

Banner '3) 回滚'
$content = [System.IO.File]::ReadAllText($cfgPath)
$log = @()

# 禁用名字含键盘相关的 kext
$pat1 = '(?s)(<key>BundlePath</key>\s*<string>[^<]*(?:Voodoo|PS2|VirtualKey|Keyboard|HID|Key)[^<]*</string>.*?<key>Enabled</key>\s*)<true\s*/>'
foreach ($m in [regex]::Matches($content, $pat1)) {
    $bp = [regex]::Match($m.Value, '(?s)<string>([^<]*)</string>').Groups[1].Value
    $log += "禁用 kext: $bp"
}
$content = [regex]::Replace($content, $pat1, '${1}<false/>')

# 复位 UEFI 键盘支持
$p = "(?s)(<key>KeySupport</key>\s*)<true\s*/>"
if ([regex]::IsMatch($content, $p)) { $content = [regex]::Replace($content, $p, '${1}<false/>'); $log += '复位 KeySupport -> false' }
foreach ($k in @('KeySupportMode','KeyTimingMode')) {
    $pk = "(?s)(<key>$k</key>\s*)<string>[^<]*</string>"
    if ([regex]::IsMatch($content, $pk)) { $content = [regex]::Replace($content, $pk, '${1}<string></string>'); $log += "清空 $k" }
}

if ($log.Count -eq 0) {
    Write-Host 'config.plist 里没发现键盘 kext / KeySupport 改动。' -ForegroundColor Yellow
    Write-Host '=> 说明上次只动了 NVRAM，直接去 OC 菜单选 Reset NVRAM 即可。' -ForegroundColor Green
} else {
    [System.IO.File]::WriteAllText($cfgPath, $content)
    $log | ForEach-Object { Write-Host "  - $_" }
    $log | Set-Content (Join-Path $backupDir 'CHANGES.txt')
    Write-Host '已写回修复后的 config.plist。' -ForegroundColor Green
}

Banner '完成'
Write-Host '重启 -> OpenCore 菜单 -> 选 macOS。若仍卡，把桌面 OC-FIX-BACKUP-* 里的 config-backup.plist 发我。'
Read-Host '按回车退出'
