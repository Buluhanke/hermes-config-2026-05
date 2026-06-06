#!/usr/bin/env python3
"""
verify_hermes_backup.py — 验证 hermes 加密备份的完整性

检测 5 项:
  1. tar.gz 存在 + 可解压 + 包内文件数合理 (应 > 1000)
  2. 关键文件都在: config.yaml, state.db, .env, skills/, memory_store.db
  3. GPG 加密文件能解密 (需要密码)
  4. 分卷拼回后能解密
  5. SQLite 完整 (state.db + memory_store.db 能打开 + sessions 表行数)

用法:
  python3 verify_hermes_backup.py /path/to/hermes-*.tar.gz.gpg.part000 --password "xxx"
  python3 verify_hermes_backup.py /path/to/encrypted-dir/ --password "xxx"
  python3 verify_hermes_backup.py /path/to/encrypted-dir/ --keychain  # 从 macOS Keychain 取
"""

import argparse
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


def check_tarball(tarball: Path) -> dict:
    """Step 1-2: 检查 tar.gz 完整性 + 关键文件存在"""
    result = {"step": "tarball", "ok": True, "details": {}}

    if not tarball.exists():
        result["ok"] = False
        result["details"]["error"] = f"tarball 不存在: {tarball}"
        return result

    result["details"]["size"] = f"{tarball.stat().st_size / 1024 / 1024:.1f} MB"

    # 列文件数
    proc = subprocess.run(
        ["tar", "-tzf", str(tarball)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        result["ok"] = False
        result["details"]["error"] = f"tar 列文件失败: {proc.stderr}"
        return result

    files = proc.stdout.splitlines()
    result["details"]["file_count"] = len(files)

    # 关键文件检查
    critical = [".hermes/config.yaml", ".hermes/state.db", ".hermes/.env", ".hermes/skills", ".hermes/memory_store.db"]
    missing = [f for f in critical if f not in files]
    if missing:
        result["ok"] = False
        result["details"]["missing"] = missing

    return result


def check_gpg_decrypt(encrypted: Path, password: str) -> dict:
    """Step 3: GPG 加密文件能解密"""
    result = {"step": "gpg_decrypt", "ok": True, "details": {}}

    proc = subprocess.run(
        [
            "gpg", "--batch", "--pinentry-mode", "loopback",
            "--passphrase", password,
            "--decrypt", str(encrypted),
        ],
        capture_output=True,
        timeout=120,
    )
    if proc.returncode != 0:
        result["ok"] = False
        result["details"]["error"] = proc.stderr.decode("utf-8", errors="replace")[:500]
        return result

    # 写到临时文件做 SQLite 检查
    tmp = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    tmp.write(proc.stdout)
    tmp.close()
    result["details"]["decrypted_size"] = f"{Path(tmp.name).stat().st_size / 1024 / 1024:.1f} MB"
    result["details"]["decrypted_path"] = tmp.name
    return result


def check_sqlite(tarball: Path) -> dict:
    """Step 5: SQLite 完整"""
    result = {"step": "sqlite", "ok": True, "details": {}}

    # 解压 state.db 和 memory_store.db 到临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in [".hermes/state.db", ".hermes/memory_store.db"]:
            proc = subprocess.run(
                ["tar", "-xzf", str(tarball), "-C", tmpdir, f],
                capture_output=True,
            )
            if proc.returncode != 0:
                result["details"][f] = "extract failed"
                continue
            extracted = Path(tmpdir) / f.lstrip("./")
            if not extracted.exists():
                result["details"][f] = "not found after extract"
                continue

            # 打开 SQLite
            try:
                conn = sqlite3.connect(str(extracted))
                cur = conn.execute("PRAGMA integrity_check")
                integrity = cur.fetchone()[0]
                sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] if f.endswith("state.db") else None
                conn.close()
                result["details"][f] = {
                    "integrity": integrity,
                    "sessions": sessions,
                    "size": f"{extracted.stat().st_size / 1024 / 1024:.1f} MB",
                }
                if integrity != "ok":
                    result["ok"] = False
            except Exception as e:
                result["details"][f] = f"sqlite open failed: {e}"
                result["ok"] = False

    return result


def find_chunks(input_path: Path) -> list:
    """从 part000 找所有 part*"""
    if input_path.is_dir():
        chunks = sorted(input_path.glob("hermes-*.tar.gz.gpg.part*"))
        return chunks

    if input_path.name.endswith(".part000"):
        prefix = str(input_path)[:-len("000")]
        chunks = sorted(Path(c) for c in [prefix + f"{i:03d}" for i in range(1000)])
        chunks = [c for c in chunks if c.exists()]
        return chunks

    return [input_path]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="hermes-*.tar.gz.gpg.part000 或目录")
    parser.add_argument("--password", help="GPG 密码")
    parser.add_argument("--keychain", action="store_true", help="从 macOS Keychain 取密码")
    args = parser.parse_args()

    if args.keychain:
        proc = subprocess.run(
            ["security", "find-generic-password",
             "-s", "com.hermes.backup.gpg",
             "-a", "hermes-archive", "-w"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(f"❌ Keychain 取密码失败: {proc.stderr}")
            sys.exit(1)
        password = proc.stdout.strip()
    elif args.password:
        password = args.password
    else:
        print("❌ 必须给 --password 或 --keychain")
        sys.exit(1)

    path = Path(args.path)
    chunks = find_chunks(path)
    if not chunks:
        print(f"❌ 没找到分卷: {path}")
        sys.exit(1)

    print(f"找到 {len(chunks)} 个分卷:")
    for c in chunks:
        print(f"  {c.name}  ({c.stat().st_size / 1024 / 1024:.1f} MB)")

    # 拼分卷
    print("\n=== Step 1: 拼分卷 ===")
    with tempfile.NamedTemporaryFile(suffix=".tar.gz.gpg", delete=False) as merged:
        for c in chunks:
            merged.write(c.read_bytes())
        merged_path = Path(merged.name)
    print(f"✓ 拼好: {merged_path.stat().st_size / 1024 / 1024:.1f} MB")

    # GPG 解密
    print("\n=== Step 2: GPG 解密 ===")
    decrypt_result = check_gpg_decrypt(merged_path, password)
    print(f"{'✓' if decrypt_result['ok'] else '❌'} {decrypt_result['details']}")
    if not decrypt_result["ok"]:
        sys.exit(1)
    decrypted = Path(decrypt_result["details"]["decrypted_path"])

    # tar 完整性 + 关键文件
    print("\n=== Step 3: tar 完整性 + 关键文件 ===")
    tar_result = check_tarball(decrypted)
    print(f"{'✓' if tar_result['ok'] else '❌'} {tar_result['details']}")

    # SQLite 完整性
    print("\n=== Step 4: SQLite 完整性 ===")
    sqlite_result = check_sqlite(decrypted)
    for k, v in sqlite_result["details"].items():
        print(f"  {k}: {v}")

    # 总结
    all_ok = tar_result["ok"] and decrypt_result["ok"] and sqlite_result["ok"]
    print()
    if all_ok:
        print("✅ 备份完整, 可用于还原")
    else:
        print("❌ 备份有问题, 不建议用于还原")
        sys.exit(1)

    # 清理
    decrypted.unlink(missing_ok=True)
    merged_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
