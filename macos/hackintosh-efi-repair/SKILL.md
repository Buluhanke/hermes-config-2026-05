---
name: hackintosh-efi-repair
description: Fix OpenCore boot from Windows when macOS won't start.
---

# Hackintosh EFI Repair (Windows-side)

## When
A Hackintosh is stuck on the Apple logo / verbose hang and the user can only reach it through the Windows install on the same box (no macOS access). Classic trigger: a previous "fix" (e.g. keyboard fix) changed OpenCore and broke boot.

## Hard constraints (user-learned — do not violate)
- **Don't make it worse.** Restore to the exact prior state; avoid piling new changes on a broken boot.
- **Agent cannot see the boot screen.** The verbose boot log must be read by the user and typed back. Design scripts to surface text the user can copy/paste.

## Topology first
Confirm disk layout on the Windows machine (admin PowerShell):
```powershell
Get-Disk | Format-Table Number,Model,PartitionStyle,OperationalStatus,Size -AutoSize
Get-Partition | Format-Table DiskNumber,PartitionNumber,Type,GptType,DriveLetter,Size -AutoSize
```
OC EFI = a ~300 MB `System` partition containing `EFI\OC\config.plist`. macOS = the `Unknown` APFS partition (`GptType 7c3457ef-...`).

## Delivery channel (no remote shell)
The Windows box typically has only SMB/RPC — no SSH/RDP/WinRM, and MS-account SMB login is **rejected** (`STATUS_LOGON_FAILURE`; `mount_smbfs` auth error). Do NOT waste time on impacket/wmiexec or SMB mounts.
Instead host the script on the assisting Mac and have the user run it in **admin PowerShell** on Windows:
```bash
# on the Mac, in a dir holding the .ps1
cd /Users/aimac/ocfix && python3 -m http.server 8000 --bind 192.168.8.112
```
```
# on the Windows machine, admin PowerShell
powershell -ep Bypass -c "irm http://192.168.8.112:8000/<script>.ps1 | iex"
```

## EFI mount — the bug that wastes a round-trip
Scan ALL EFI partitions. **Mount one at a time with a fresh drive letter, then `remove` it before probing the next.**
Bug seen in the wild: a script grabbed `Z:` on the first EFI and never released it, so the second EFI (the real OC one) could not mount → reported "OC EFI not found". Always `select disk N` + `select partition N` + `assign letter=Y` ... then `remove` after each probe. Reuse letters Y:/X:/W:/V:/U: in a loop.

## Diagnostic: enable verbose, read the LAST line
Add `-v` to `boot-args`, reboot → OpenCore → macOS. User copies the **last line** of white text.
- `vnode_lookup /System/Library/dyld/ failed (error=2)` at the `launchd` stage ⇒ **system volume (APFS) file corruption**, NOT OpenCore/config. Reaching `launchd` proves kernel + all kexts loaded fine. Fix = **macOS Recovery → Disk Utility → top-level APFS container → First Aid** (user does this at the machine; agent can't).
- Other kext/ACPI/`panic` lines ⇒ different cause; triage per line.

## Restore (pure) before anything else
1. Backup the whole EFI to Desktop before any write.
2. Restore the pre-change `config.plist` byte-for-byte, **zero edits**.
3. **Do NOT whitelist-disable kexts blindly.** On real setups AMFIPass / IOSkywalkFamily / IO80211FamilyLegacy / USBToolBox / UTBDefault / UTBMap are legitimate and required. A "fix keyboard" kext may already be absent from config — disabling good kexts only makes it worse.
4. If `AMFIPass.kext` is present, ensure `amfipass=1` is in `boot-args` (Sonoma/Sequoia require it; its absence can itself cause dyld errors).

## Backup-timestamp trap
Self-generated backups are stamped with the script's run time. The **true original** is the backup captured *before any modification* (e.g. `OC-FIX-BACKUP-031659`), NOT the one with the earliest-looking mtime. Don't trust mtime ordering of your own backups.
The user's "backup from before the break" may live on the **Hackintosh EFI itself** (where the fixing Hermes stored it), not on the Windows desktop. Scan ALL files on every EFI partition (not just `*.plist`) for PRE-TODAY entries to find it.

## References
- `references/machine-2026-08.md` — this user's exact topology + the find-backup2 scan snippet.
