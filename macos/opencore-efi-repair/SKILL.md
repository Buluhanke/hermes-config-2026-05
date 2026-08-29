---
name: opencore-efi-repair
description: Repair Hackintosh stuck at Apple logo via another PC's EFI.
---

# OpenCore / Hackintosh EFI Repair (remote, from Windows)

## When this applies
- Black Apple (Hackintosh) machine is **not** the one you're working from; it's stuck at the Apple logo / frozen progress bar after a prior tweak (e.g. "fixed keyboard", added a kext, changed UEFI input).
- The macOS disk is attached to (or dual-boots with) a **Windows** machine you can reach over LAN, OR a macOS recovery USB can be made.
- Symptom "stuck at Apple logo, progress only a few %" = kernel/kext/driver load failure during early boot, **before** the login screen. Not a password issue.

## Root-cause model (from a real case)
A prior "fix keyboard" edit did ONE of:
1. Added a keyboard kext (VoodooPS2Controller / VirtualKey / a virtual-keyboard driver) to `Kernel/Add` and left it `Enabled=true` → kernel panics/hangs at logo.
2. Changed `UEFI/Input/KeySupport` to `true` or set `KeySupportMode`/`KeyTimingMode` → input layer hangs pre-boot.
3. Only mutated NVRAM variables (no config change) → fixed by Reset NVRAM alone.
Most reliable fix addresses #1 + #2 together; #3 is the fallback.

## Route A — macOS recovery USB (cleanest, no Windows needed)
1. On any Mac/Windows, build a macOS installer/Recovery USB (BalenaEtcher writes official DMG; Windows uses TransMac).
2. Boot the Hackintosh from it → Terminal: `diskutil list` (note EFI, usually disk0s1) → `mkdir /tmp/efi; mount -t msdos /dev/diskNs1 /tmp/efi` → edit `/tmp/efi/EFI/OC/config.plist`.
3. macOS native `mount_msdos` is more reliable than Windows for FAT32 EFI. Prefer this if the disk can reach a Mac.

## Route B — Mount EFI from Windows (the LAN case)
Windows sees the Hackintosh disk (e.g. Disk 1) with **two EFI partitions** when dual-booting; only one holds `OC\config.plist`.

**Step 1 — deliver the repair script cross-OS.** From the Mac you're on:
```bash
# serve the script; Windows pulls it over LAN (no file copy, no email)
cd <dir-with-fix-oc-efi.ps1>
python3 -m http.server 8000 --bind <MAC_LAN_IP>   # e.g. 192.168.8.112
```
On the Windows box (run **as Administrator** PowerShell):
```powershell
powershell -ep Bypass -c "irm http://<MAC_LAN_IP>:8000/fix-oc-efi.ps1 | iex"
```
The script (see `scripts/fix-oc-efi.ps1`) does everything below automatically.

**Step 2 — what the script does (manual equivalent if you must type it):**
1. Enumerate ALL EFI System partitions: `Get-Partition | ? GptType -eq 'c12a7328-f81f-11d2-ba4b-00a0c93ec93b'`.
2. Mount each via diskpart `assign letter=Z` until one contains `EFI\OC\config.plist` (skip CLOVER-only / Windows EFI).
3. **Backup first**: copy `config.plist` to Desktop `OC-FIX-BACKUP-<ts>` + `Compress-Archive` the whole EFI. Zero-risk rollback.
4. **Rollback**:
   - **Whitelist method (critical)**: list every `Kernel/Add` entry's `BundlePath`; kexts whose name does NOT contain a standard substring (Lilu, VirtualSMC, WhateverGreen, AppleALC, IntelMausi, NVMeFix, USBInjectAll, HfsPlus, OpenRuntime, OpenCanopy, etc.) are "EXTRA" → set their `Enabled` to `<false/>`. This disables the keyboard fix's added kext even if its name is unexpected.
   - Reset `UEFI/Input/KeySupport` → `<false/>`; clear `KeySupportMode`/`KeyTimingMode` to empty string.
   - Add `-v` to `NVRAM/Add/.../boot-args` (verbose boot) so the next hang shows the last loaded item in white text.
5. Unmount EFI, report changes.

**Step 3 — verify by booting.** Reboot the Hackintosh → OpenCore menu → macOS.
- Boots → done.
- Still stuck → at OC menu press **SPACE** to reveal tools → **Reset NVRAM** → boot macOS again.
- Still stuck → send `Desktop\OC-FIX-BACKUP-*\config-backup.plist` to the assistant for a line-level review.

## Pitfalls (learned the hard way)
- **Do NOT only reset KeySupport** (an earlier v2 did this and the machine stayed stuck — the real culprit was the added kext the keyword regex never matched). Always use the **whitelist** disable of ALL non-standard kexts.
- **PowerShell console shows Chinese as mojibake** (`æ¾ä¸å°`) under default codepage — harmless, logic still runs. Keep script output in ASCII/English to stay readable.
- **macOS has no `timeout` command** — wrap remote commands in Python `subprocess.run(..., timeout=50)` instead of `timeout 50 ...`.
- **impacket `wmiexec.py` remote shell fails with `STATUS_LOGON_FAILURE`** if the Windows login is a **Microsoft account** (not a local account) — WMI won't accept it. Use the HTTP-served-script route (Route B) instead of trying to remote in. Local accounts (`.\user`) sometimes work but aren't guaranteed.
- **`wmiexec.py` flag parsing**: pass the command as separate args, not `-c "..."` (it collides with `-codec`/`-com-version`). Use `wmiexec.py user:pass@host "cmd & cmd"`.
- EFI partitions may already have a drive letter or be "Offline" — the script's diskpart `assign` loop handles letter assignment; if a disk shows `OperationalStatus=Offline`, `Set-Disk -IsOffline $false` first.

## Verification
- Script prints `>>> Hackintosh EFI found: disk N partition M (Z:)` and a `KEXTS:` list tagged `STD`/`EXTRA` with `-> disable extra kext:` lines → change applied.
- After reboot, either macOS loads (success) or verbose text freezes at a named kext/driver (tells you the remaining culprit).

## References
- `references/session-diagnostics.md` — real Get-Disk/Get-Partition output from the 2026-08-29 case (Disk 1 ZHITAI Ti600 1TB, two EFI parts, APFS GUID `7c3457ef...`), plus the v2-vs-v3 miss.
- `scripts/fix-oc-efi.ps1` — the working repair script (whitelist + KeySupport + -v). Copy to a served dir and run on the Windows box.
