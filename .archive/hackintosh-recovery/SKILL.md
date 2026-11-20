---
name: hackintosh-recovery
description: Use when Hackintosh stuck at Apple logo post-OpenCore edit.
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [hackintosh, opencore, efi, windows, recovery, sysadmin]
    related_skills: [windows-wmi-exec]
---

# Hackintosh Recovery (OpenCore)

## Symptom → cause
Stuck at Apple logo with only a few % progress after a "keyboard fix" = `config.plist` mutated (new keyboard kext, or `UEFI/Input` keyboard support changed) OR only NVRAM written. 99% fixable by rollback — no reinstall.

## Try first (zero-risk, 10s)
Boot → OpenCore picker → press **Space** to reveal tools → **Reset NVRAM** → reboot → pick macOS. If the break was only an NVRAM variable, this alone restores boot.

## Path A — macOS recovery USB
1. Make a macOS installer/recovery USB (BalenaEtcher on Mac/Win, or TransMac on Windows).
2. Boot target → USB → Utilities → Terminal:
   ```sh
   diskutil list
   mkdir /tmp/efi; mount -t msdos /dev/disk0s1 /tmp/efi
   cp /tmp/efi/EFI/OC/config.plist ~/Desktop/oc-broken.plist
   ```
3. Send `oc-broken.plist` to the assistant → precise line-level rollback.

## Path B — from Windows (box only boots Windows)
1. Connect the Hackintosh system disk to the Windows machine (USB adapter, or dual-boot).
2. Run `scripts/fix-oc.ps1` as Administrator — it will:
   - locate the EFI System Partition (GPT `C12A7328-F81F-11D2-BA4B-00A0C93EC93B`) and assign a letter
   - **back up the whole EFI to Desktop `OC-FIX-BACKUP-<ts>`** (config + full zip) — zero-risk
   - disable newly-added keyboard kext (Voodoo/PS2/VirtualKey/Key/HID in `BundlePath`)
   - reset `UEFI/Input/KeySupport` → false and clear `KeySupportMode`/`KeyTimingMode`
   - write back fixed `config.plist`
3. Reboot → OpenCore → macOS.

Run from Windows (e.g. via windows-wmi-exec):
```
powershell -ep Bypass -c "irm http://<HOST>/fix-oc.ps1 | iex"
```

## Manual config.plist reverts
- `Kernel/Add`: new keyboard kext entry → `Enabled=false` or delete
- `UEFI/Input/KeySupport` → `false`
- `UEFI/Input/KeySupportMode` → empty
- `NVRAM/Add/7C436110-…/boot-args`: drop anything non-basic added during the fix

## Pitfalls
- Always back up EFI before editing (script does it automatically).
- Script reports "no keyboard kext / KeySupport changes found" but boot still fails → it was NVRAM-only; just Reset NVRAM from the picker.
- EFI is FAT32; Windows `diskpart` `assign letter=` is the reliable mount path when the partition has no letter.
- Don't mount a dirty EFI read-write from macOS; mount readOnly first to inspect.

## Support files
- `scripts/fix-oc.ps1` — Windows-side EFI mount + OpenCore keyboard-kext rollback (auto-backup).
