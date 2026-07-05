# alpha-forge-launcher

[AlphaForge](https://alforgelabs.com/) のバックテスト CLI バイナリを取得・起動する薄いランチャーです（Apache-2.0・依存ゼロ）。インストールすると `alpha-forge` コマンドを提供します。

[![Follow @Alforge_bot](https://img.shields.io/badge/Follow-%40Alforge__bot-000?logo=x)](https://x.com/Alforge_bot)

> PyPI 配布名は `alpha-forge-launcher` です（`alpha-forge` は既存の無関係プロジェクト `alphaforge` への PyPI 類似名ガードで登録できないため）。提供するコマンドは `alpha-forge`（正準）のまま維持しています。

```bash
# uvx（インストール不要で実行）
uvx alpha-forge-launcher --version
uvx alpha-forge-launcher system init && uvx alpha-forge-launcher demo
# または --from でコマンド名を明示
uvx --from alpha-forge-launcher alpha-forge --version

# pip（インストール後は alpha-forge コマンドが使える）
pip install alpha-forge-launcher
alpha-forge --version
alpha-forge system init && alpha-forge demo
```

- 起動時に対応プラットフォームのバイナリを [Releases](https://github.com/alforge-labs/alforge-labs.github.io/releases) から取得し、SHA256 検証のうえキャッシュして実行します。2 回目以降はキャッシュを再利用します。
- **対応プラットフォーム（現時点）**: macOS arm64。他は順次対応。
- **バージョン同期**: 既定で最新 Release を追従します。固定するには `ALPHA_FORGE_VERSION=v0.17.0 alpha-forge ...`。ランチャー自身のバージョンはランチャーのコード変更時のみ更新します。

AlphaForge 本体は商用ライセンス（無料 Trial あり）。ライセンスは実行時にバイナリが管理します。
