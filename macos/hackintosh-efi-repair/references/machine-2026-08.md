# Machine topology — 2026-08 (idluq dual-boot)

## Network / access
- Assisting Mac: 192.168.8.112 (en0). Hosts `python3 -m http.server 8000 --bind 192.168.8.112` to serve `.ps1`.
- Target Windows: 192.168.8.123. No SSH/RDP/WinRM; MS-account SMB login rejected. User `idluq`.
- Port scan from Mac: 445/139 open (SMB), 22/3389/135 closed. `mount_smbfs //idluq:3308@192.168.8.123/C$` → auth error.

## Disk layout (Windows side, 2026-08)
- Disk 0: Dahua NVMe 2TB — Windows data drives D:/E:/F: (NOT Hackintosh).
- Disk 1: ZHITAI Ti600 1TB (Hackintosh):
  - part1  System EFI 300MB  (Windows boot EFI — no OC)
  - part3  Basic  C: 268GB    (Windows OS)
  - part10 System EFI 300MB  → **OC EFI** (`EFI\OC\config.plist`)  ← edit this
  - part11 Unknown APFS 297GB → **macOS system volume** (the one that corrupted)

## Symptom → diagnosis
- Stuck on Apple logo. Verbose hang line:
  `shared_region: 0x... [1(L launchd)]: vnode_lookup(/System/Library/dyld/) failed (error=2)`
- Meaning: system volume file corruption (error=2 = file not found). Kernel + all 16 kexts already loaded (we're at launchd). NOT a config/kext problem. Fix = macOS Recovery First Aid on the APFS container.

## Kext inventory (config.plist, 16 entries)
Lilu, VirtualSMC, AMFIPass, IOSkywalkFamily, IO80211FamilyLegacy (+AirPortBrcmNIC plugin), NVMeFix, RealtekRTL8111, RestrictEvents, SMCProcessor, SMCSuperIO, USBToolBox, UTBDefault, XHCI-unsupported, AppleALC, UTBMap.
→ AMFIPass / IOSkywalkFamily / IO80211FamilyLegacy / USBToolBox / UTBDefault / UTBMap are **LEGIT, do not disable**.

## Backups found (all self-generated 2026-08-29, ~24KB)
- `OC-FIX-BACKUP-20260829-031659` → **true original** (captured before any modification)
- `OC-FIX4-BACKUP-20260829-103923` → post-fix-oc2 state (KeySupport already cleared)
- `OC-FIX5-PREV4-20260829-105419` → post-v4 state
- No pre-break "small backup" on Windows side → likely on the Hackintosh EFI itself.

## find-backup2 scan (list ALL EFI files, flag PRE-TODAY)
Full script: `/Users/aimac/ocfix/find-backup2.ps1` (hosted same way). Logic:
```powershell
# for each disk -> each System partition:
#   assign fresh letter (Y:/X:/W:/V:/U:/T:/S:), Get-ChildItem -Recurse -File
#   flag LastWrite -lt [datetime]'2026-08-29 00:00:00'  (PRE-TODAY)
#   flag name -match 'backup|config.*\d|old|\.bak|\.prev|before|pre'
# unmount (remove) after each partition; also scan Desktop for pre-today files
# Small (<24000 B) PRE-TODAY entry = the sought "before" backup.
```
