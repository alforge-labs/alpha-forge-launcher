import hashlib
import io
import tarfile

import pytest

from alpha_forge_launcher import bootstrap


def test_resolve_artifact_macos_arm64(monkeypatch):
    monkeypatch.setattr(bootstrap.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(bootstrap.platform, "machine", lambda: "arm64")
    assert bootstrap._resolve_artifact() == "alpha-forge-macos-arm64"


def test_resolve_artifact_unsupported_exits(monkeypatch, capsys):
    monkeypatch.setattr(bootstrap.platform, "system", lambda: "Linux")
    monkeypatch.setattr(bootstrap.platform, "machine", lambda: "x86_64")
    with pytest.raises(SystemExit) as ei:
        bootstrap._resolve_artifact()
    assert ei.value.code == 1
    err = capsys.readouterr().err
    assert "linux-x86_64" in err
    assert "alforgelabs.com" in err


def test_resolve_version_env_pin(monkeypatch):
    monkeypatch.setenv("ALPHA_FORGE_VERSION", "v0.17.0")
    assert bootstrap._resolve_version() == "v0.17.0"


def test_resolve_version_fetches_latest(monkeypatch):
    monkeypatch.delenv("ALPHA_FORGE_VERSION", raising=False)

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"tag_name": "v0.99.0"}'

    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert bootstrap._resolve_version() == "v0.99.0"


def test_verify_sha256_mismatch_exits(monkeypatch, tmp_path):
    archive = tmp_path / "a.tar.gz"
    archive.write_bytes(b"hello")

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b"deadbeef  a.tar.gz"

    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", lambda *a, **k: _Resp())
    with pytest.raises(SystemExit):
        bootstrap._verify_sha256(archive, "https://x/a.tar.gz")


def test_verify_sha256_match_passes(monkeypatch, tmp_path):
    archive = tmp_path / "a.tar.gz"
    archive.write_bytes(b"hello")
    digest = hashlib.sha256(b"hello").hexdigest()

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return f"{digest}  a.tar.gz".encode()

    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", lambda *a, **k: _Resp())
    bootstrap._verify_sha256(archive, "https://x/a.tar.gz")  # 例外が出なければ OK


def test_safe_extract_rejects_traversal(tmp_path):
    bad = tmp_path / "bad.tar.gz"
    with tarfile.open(bad, "w:gz") as tar:
        data = b"x"
        info = tarfile.TarInfo(name="../escape.txt")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    with pytest.raises(SystemExit):
        bootstrap._safe_extract(bad, tmp_path / "out")


def test_run_execs_cached_binary(monkeypatch, tmp_path):
    # キャッシュ済みバイナリがあれば DL せず execv される
    monkeypatch.setattr(bootstrap, "_resolve_artifact", lambda: "alpha-forge-macos-arm64")
    monkeypatch.setattr(bootstrap, "_resolve_version", lambda: "v0.17.0")
    monkeypatch.setattr(bootstrap, "_cache_root", lambda: tmp_path)
    binary = tmp_path / "v0.17.0" / "forge.dist" / "forge"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)

    called = {}
    monkeypatch.setattr(bootstrap.os, "execv", lambda p, a: called.update(path=p, argv=a))
    bootstrap.run(["--version"])
    assert called["path"] == str(binary)
    assert called["argv"] == ["alpha-forge", "--version"]
