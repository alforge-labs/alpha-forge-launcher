# alpha-forge (launcher)

`uvx alpha-forge ...` / `pip install alpha-forge` で [AlphaForge](https://alforgelabs.com/) のバックテスト CLI バイナリを取得・起動する薄いランチャーです（Apache-2.0）。

```bash
uvx alpha-forge --version
uvx alpha-forge system init && uvx alpha-forge demo
```

- 起動時に対応プラットフォームのバイナリを [Releases](https://github.com/alforge-labs/alforge-labs.github.io/releases) から取得し、SHA256 検証のうえキャッシュして実行します。2 回目以降はキャッシュを再利用します。
- **対応プラットフォーム（現時点）**: macOS arm64。他は順次対応。
- **バージョン同期**: 既定で最新 Release を追従します。固定するには `ALPHA_FORGE_VERSION=v0.17.0 uvx alpha-forge ...`。ランチャー自身のバージョンはランチャーのコード変更時のみ更新します。

AlphaForge 本体は商用ライセンス（無料 Trial あり）。ライセンスは実行時にバイナリが管理します。
