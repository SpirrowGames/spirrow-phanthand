# Phanthand

[![English](https://img.shields.io/badge/lang-English-blue)](README.md)

開発PC上のファイルに軽量なAPIアクセスを提供するサーバーです。リモートサーバー上のAIエージェントがローカルマシンのソースコードを読み取る、AI支援開発ワークフロー向けに設計されています。

## 特徴

- **読み取り専用** — ファイル読み込み、ディレクトリ一覧、globパターン検索
- **パスホワイトリスト** — 明示的に許可されたディレクトリのみアクセス可能
- **Bearerトークン認証** — シンプルなAPIキー保護
- **ゼロコンフィグ** — YAML設定ファイル1つ、データベース不要

## クイックスタート

### 前提条件

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)（推奨）または pip

### セットアップ

```bash
git clone https://github.com/SpirrowGames/spirrow-phanthand.git
cd spirrow-phanthand

# 設定ファイルをテンプレートからコピー
cp config.example.yaml config.yaml
# config.yaml を編集 — APIキーと許可パスを設定
```

### 起動

```bash
# uv の場合（推奨）
uv run phanthand

# pip の場合
pip install -e .
python -m phanthand
```

## 設定

`config.yaml` を編集してください：

```yaml
server:
  host: "0.0.0.0"    # リッスンアドレス
  port: 7300          # リッスンポート

security:
  api_key: "your-secret-key"    # Bearerトークン
  allowed_paths:                 # アクセス許可ディレクトリ
    - "D:/Projects"
    - "C:/Dev/my-project"
  max_file_size_mb: 10           # 読み取り最大ファイルサイズ (MB)
```

> **注意:** `config.yaml` はgitignoreされています。`config.example.yaml` のみがリポジトリで管理されます。

## APIエンドポイント

### システム

| メソッド | パス | 認証 | 説明 |
|---------|------|------|------|
| GET | `/health` | 不要 | ヘルスチェック |

### ファイル操作

全てのファイルエンドポイントは `Authorization: Bearer <api_key>` ヘッダーが必要です。

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/files/read` | テキストファイル読み込み |
| POST | `/files/list` | ディレクトリ一覧 |
| POST | `/files/exists` | ファイル/ディレクトリ存在確認 |
| POST | `/files/info` | ファイルメタデータ取得 |
| POST | `/files/tree` | 再帰ディレクトリツリー |
| POST | `/files/search` | globパターン検索 |

### 使用例

```bash
# ヘルスチェック
curl http://localhost:7300/health

# ファイル読み込み
curl -X POST http://localhost:7300/files/read \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"path": "D:/Projects/my-app/src/main.py"}'
```

### レスポンス形式

全レスポンスは統一されたフォーマットで返却されます：

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

## セキュリティ

- 全ファイル操作は `allowed_paths` に列挙されたパスに制限されます
- シンボリックリンクによるトラバーサルはパス解決により防止されます
- ファイル読み込みは `max_file_size_mb` で制限されます
- 書き込み操作は一切サポートされていません

## ライセンス

MIT License — 詳細は [LICENSE](LICENSE) を参照してください。
