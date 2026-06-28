"""alpha-forge ランチャー: プラットフォーム判定→Releases からバイナリ取得→検証→exec。

純標準ライブラリのみ。proprietary コードは含まず、実体は AlphaForge バイナリ
（Whop ライセンスは実行時にバイナリが強制する）。
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

_RELEASES_REPO = "alforge-labs/alforge-labs.github.io"
_LATEST_API = f"https://api.github.com/repos/{_RELEASES_REPO}/releases/latest"
_DOCS_URL = "https://alforgelabs.com/"
_HTTP_TIMEOUT = 30

# (system, machine) → アーティファクト名（拡張子 .tar.gz）。現状 macOS-arm64 のみ配布。
# 新プラットフォームのバイナリが Releases に追加されたらここに 1 行足す。
_ARTIFACTS: dict[tuple[str, str], str] = {
    ("Darwin", "arm64"): "alpha-forge-macos-arm64",
}


def _resolve_artifact() -> str:
    key = (platform.system(), platform.machine())
    artifact = _ARTIFACTS.get(key)
    if artifact is None:
        plat = f"{key[0].lower()}-{key[1].lower()}"
        sys.stderr.write(
            f"alpha-forge: No alpha-forge binary published for {plat} yet.\n"
            f"  Currently supported: macOS arm64.\n"
            f"  See {_DOCS_URL} for installation options.\n"
        )
        raise SystemExit(1)
    return artifact


def _resolve_version() -> str:
    pinned = os.environ.get("ALPHA_FORGE_VERSION", "").strip()
    if pinned:
        return pinned
    try:
        with urllib.request.urlopen(_LATEST_API, timeout=_HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(
            f"alpha-forge: failed to fetch the latest version from GitHub: {exc}\n"
            "  Check your network, or pin a version with ALPHA_FORGE_VERSION=vX.Y.Z.\n"
        )
        raise SystemExit(1) from exc
    tag = data.get("tag_name")
    if not tag:
        sys.stderr.write("alpha-forge: could not determine the latest version (no tag_name).\n")
        raise SystemExit(1)
    return str(tag)


def _cache_root() -> Path:
    base = os.environ.get("XDG_CACHE_HOME", "").strip()
    root = Path(base) if base else Path.home() / ".cache"
    return root / "alpha-forge"


def _verify_sha256(archive: Path, base_url: str) -> None:
    """``<base_url>.sha256`` を取得して検証。取得不能なら警告して続行。"""
    try:
        with urllib.request.urlopen(base_url + ".sha256", timeout=_HTTP_TIMEOUT) as resp:
            expected = resp.read().decode().split()[0].strip().lower()
    except Exception:  # noqa: BLE001
        sys.stderr.write("alpha-forge: could not fetch SHA256 checksum; skipping verification.\n")
        return
    actual = hashlib.sha256(archive.read_bytes()).hexdigest().lower()
    if actual != expected:
        sys.stderr.write(
            "alpha-forge: SHA256 checksum mismatch (possible tampering/corruption).\n"
            f"  expected: {expected}\n  actual:   {actual}\n"
        )
        raise SystemExit(1)


def _safe_extract(archive: Path, dest: Path) -> None:
    """path traversal を防いで tar.gz を dest へ展開する（CVE-2007-4559 対策）。"""
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            target = (dest / member.name).resolve()
            if target != dest_resolved and not str(target).startswith(str(dest_resolved) + os.sep):
                sys.stderr.write(f"alpha-forge: unsafe path in archive: {member.name}\n")
                raise SystemExit(1)
        tar.extractall(dest)  # noqa: S202 (上で全メンバを検証済み)


def _strip_quarantine(forge_dist: Path) -> None:
    if platform.system() != "Darwin":
        return
    try:
        subprocess.run(
            ["xattr", "-dr", "com.apple.quarantine", str(forge_dist)],
            check=False,
            capture_output=True,
        )
    except Exception:  # noqa: BLE001
        pass


def _ensure_binary(version: str, artifact: str) -> Path:
    """バイナリをキャッシュへ用意し、``forge.dist/forge`` の Path を返す。"""
    version_dir = _cache_root() / version
    binary = version_dir / "forge.dist" / "forge"
    if binary.exists() and os.access(binary, os.X_OK):
        return binary  # キャッシュヒット（再 DL しない）

    base_url = (
        f"https://github.com/{_RELEASES_REPO}/releases/download/{version}/{artifact}.tar.gz"
    )
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "archive.tar.gz"
        sys.stderr.write(f"alpha-forge: downloading {artifact}.tar.gz ({version})...\n")
        with urllib.request.urlopen(base_url, timeout=_HTTP_TIMEOUT) as resp:
            archive.write_bytes(resp.read())
        _verify_sha256(archive, base_url)
        _safe_extract(archive, version_dir)
    if not (binary.exists() and os.access(binary, os.X_OK)):
        sys.stderr.write(
            "alpha-forge: forge.dist/forge not found or not executable after extraction.\n"
        )
        raise SystemExit(1)
    _strip_quarantine(version_dir / "forge.dist")
    return binary


def run(argv: list[str]) -> None:
    artifact = _resolve_artifact()
    version = _resolve_version()
    binary = _ensure_binary(version, artifact)
    os.execv(str(binary), ["alpha-forge", *argv])
