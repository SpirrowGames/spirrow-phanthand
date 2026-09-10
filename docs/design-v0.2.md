---
id: spirrow-phanthand:design-v0.2
title: Phanthand 設計ドキュメント v0.2
product: spirrow-phanthand
type: spec
status: active
version: 0.2
created: 2026-02-08
last_verified: 2026-09-10
supersedes: []
related: [platform:infra-registry]
keywords: [Phanthand, 設計, FastAPI, Tailscale, MagicKit, ファイル読み取り, 常駐サーバ]
legacy_drive_id: [1zezrvUkn9yucLYIIFmmR0Uj0OLe0vmo3iwLbG7EsSzo]
---

# Phanthand - 設計ドキュメント v0.2

## 概要

Phanthandは開発PC上で動作する軽量な常駐HTTPサーバ。リモートサーバ（{{HOST_SERVICES}}）上のMagicKitワークフローから、開発PCのローカルファイルを読み取るためのAPIを提供する。

「見えざる手（Phantom Hand）」として、AIが開発PCのリソースに透過的にアクセスできるようにする。

## 設計原則

1. **ミニマル**: 今必要なのはファイル読み取り。構造は拡張可能に、実装は最小に
2. **ステートレス**: Phanthand自体は状態を持たない汎用エージェント
3. **URL直指定**: MagicKitからURL指定で呼び出す。レジストリ等の状態管理不要
4. **複数PC対応**: 同じPhanthandをどのPCにもインストールするだけで動く

## 主要な設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| ツール名 | Phanthand (Phantom + Hand) | SpirrowPlatform命名規則に合致 |
| 言語 | Python 3.12+ (FastAPI) | SpirrowPlatform統一・開発速度 |
| 接続方式 | URL直指定 | AIが呼ぶので人間の認知負荷は無関係。レジストリ不要で疎結合 |
| 初回スコープ | ファイル読み取り系6エンドポイント | YAGNI原則。必要になったら拡張 |
| セキュリティ | Tailscale VPN + Bearer Token + パスホワイトリスト | 姿勢と、その判断の根拠は [[platform:infra-registry]] §5（規約 §3.1-4 により本書には書かない） |
| APIキー | 全PC共通 | 同上 |
| MagicKit連携 | spirrow-magickit:phanthand_* ツール | MagicKitワークフローから直接呼び出し可能 |
| 常駐化 | NSSM (Windows Service) | PC起動時に自動起動 |

## アーキテクチャ

MagicKit ({{HOST_SERVICES}}) → HTTP (Tailscale VPN) → Phanthand (各開発PC :7300)

複数PCそれぞれにPhanthandをインストール。MagicKitからURLで直接指定して呼び出す。

## API設計 (v0.1)

| Method | Path | 説明 |
|--------|------|------|
| GET | /health | ヘルスチェック・疎通確認 |
| POST | /files/read | ファイル読み取り |
| POST | /files/list | ディレクトリ一覧 |
| POST | /files/exists | ファイル存在確認 |
| POST | /files/info | ファイルメタ情報 |
| POST | /files/tree | ディレクトリツリー |
| POST | /files/search | パターン検索（glob） |

## 将来拡張枠

- ファイル書き込み (/files/write, /files/copy, /files/move, /files/delete)
- コマンド実行 (/commands/exec, /commands/exec-async)
- MCP Server化
- WebSocket (stdout streaming)

## プロジェクト構成

spirrow-phanthand/
├── phanthand/
│   ├── main.py (FastAPI app & uvicorn)
│   ├── config.py (config.yaml読み込み)
│   ├── auth.py (Bearer Token認証)
│   ├── models.py (Pydanticモデル)
│   ├── routers/ (system.py, files.py)
│   └── services/ (file_service.py)
├── config.yaml
├── requirements.txt
└── README.md

## セキュリティ

本節の実内容は [[platform:infra-registry]] §5 にある。conventions §3.1-4 により、
認証の姿勢（何で守られていて、何に依存しているか）は public リポジトリに書かず
台帳へ集約する。

Phanthand が持つ制御そのものは 4 つ: tailnet IP への bind / Bearer Token
（環境変数 `PHANTHAND_API_KEY`）/ パスホワイトリスト（`config.yaml` の許可
ディレクトリ）/ ファイルサイズ制限（既定 10MB）。

## 移行時の注記（2026-09-10）

Drive 原本（`1zezrvUkn9yucLYIIFmmR0Uj0OLe0vmo3iwLbG7EsSzo`）の移行。

**この repo には移行前 Markdown が `README.md` / `README.ja.md` の 2 本しか無く、
設計書に当たるものが無かった**（[[platform:reconciliation-small-projects]] §1）。
`docs/` はこの移行で新設した。README には設計判断の記述が無い（「設計決定」も
「Tailscale」も 0 hit）ので、本書は重複ではない。

### 逐語からの逸脱 3 箇所

| 箇所 | 対応 | 根拠 |
|---|---|---|
| §概要 / §アーキテクチャ の実ホスト名 2 件 | `{{HOST_SERVICES}}` に置換 | conventions §3.1-2 |
| §主要な設計決定 の「セキュリティ」「APIキー」の理由列 | [[platform:infra-registry]] §5 への参照に置換 | **§3.1-4（置換ではなく移動）** |
| §セキュリティ 本文 | 同上。持っている制御 4 つは残し、姿勢と根拠は台帳へ | 同上 |

**移した内容の要点**: API キーが全開発 PC で共通であること、そしてそれが
「tailnet 内なので十分」という判断の上に立っていること。1 台からキーが漏れれば
全 PC のファイル読み取り経路が開く。台帳側にはこの判断の根拠ごと記録してある
（`spirrow-docs#22`）。**姿勢だけ書いて根拠を捨てると、後から再検討できない。**

ポート `7300` は実値のまま残した（§3.1-3: ホスト名を伏せた時点でポート番号は
指す先を失う）。台帳 §3 に対応を追加してある。

### 設計と実装は一致している

| 本書 | 現物 |
|---|---|
| §プロジェクト構成 | `phanthand/{main,config,auth,models}.py` / `routers/{system,files}.py` / `services/file_service.py` — **全て一致** |
| §API設計 の 7 エンドポイント | `routers/system.py` の `GET /health` + `routers/files.py` の `POST /{read,list,exists,info,tree,search}` — **7 本とも実在** |

`config.yaml` は repo では `config.example.yaml` として置かれている（実設定は
`.gitignore` 対象）。`requirements.txt` は `pyproject.toml` になった。

**§将来拡張枠（書き込み / コマンド実行 / MCP Server 化 / WebSocket）は未実装。**
`routers/` に書き込み系は無い。∴ 本書は「読み取り専用である」ことの根拠でもある —
§設計原則 1 の「今必要なのはファイル読み取り。構造は拡張可能に、実装は最小に」が
守られている状態。
