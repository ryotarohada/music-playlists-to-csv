# Spotify to Google Sheets 同期システム仕様書

## 1. システム概要

Spotify のプレイリストを Google Sheets に自動同期する Python スクリプト。GitHub Actions で定期実行。

## 2. 機能要件

### 2.1 基本機能

- Spotify の指定プレイリストから曲情報を取得
- Google Sheets に差分データのみ追加（重複排除）
- 既存データ（ユーザーのメモ含む）は保持
- 削除された曲もシート上に残す（履歴として）

### 2.2 自動実行

- GitHub Actions で 15 分ごとに自動実行
- 手動実行も可能（workflow_dispatch）

## 3. データ仕様

### 3.1 Google Sheets カラム構成

| カラム名     | 型     | 説明                                       | 自動/手動 |
| ------------ | ------ | ------------------------------------------ | --------- |
| アーティスト | String | アーティスト名（複数の場合は ", " で結合） | 自動      |
| アルバム     | String | アルバム名                                 | 自動      |
| 曲名         | String | トラック名                                 | 自動      |
| メモ         | String | ユーザーが自由に記入するメモ欄             | 手動      |
| 追加日       | String | シートに追加された日付（YYYY/MM/DD 形式）  | 自動      |

### 3.2 重複判定ロジック

```python
# アーティスト名 + 曲名 の組み合わせで一意性を判定
unique_key = f"{artist_name}_{track_name}"
```

### 3.3 データ更新ルール

- **新曲**: シートの最下行に追加
- **既存曲**: 一切変更しない（メモ保護）
- **削除曲**: シート上にそのまま残す（削除フラグなし）

## 4. API 仕様

### 4.1 Spotify API

- **認証方式**: Client Credentials Flow
- **必要な権限**: プレイリスト読み取り
- **取得エンドポイント**: `/playlists/{playlist_id}/tracks`
- **取得データ**:
  - track.name（曲名）
  - track.artists（アーティスト配列）
  - track.album.name（アルバム名）

### 4.2 Google Sheets API

- **認証方式**: Service Account
- **必要な権限**: スプレッドシート読み書き
- **使用ライブラリ**: gspread
- **操作**:
  - `get_all_records()`: 既存データ取得
  - `append_rows()`: 新規データ追加

## 5. 環境設定

### 5.1 必要な認証情報（GitHub Secrets）

| Secret 名             | 説明                           | 例                               |
| --------------------- | ------------------------------ | -------------------------------- |
| SPOTIFY_CLIENT_ID     | Spotify App の Client ID       | 1234567890abcdef...              |
| SPOTIFY_CLIENT_SECRET | Spotify App の Client Secret   | abcdef1234567890...              |
| GOOGLE_CREDENTIALS    | Service Account の JSON 全体   | {"type": "service_account", ...} |
| SPOTIFY_PLAYLIST_ID   | 対象の Spotify プレイリスト ID | 37i9dQZF1DXcBWIGoYBM5M           |
| GOOGLE_SPREADSHEET_ID | 書き込み先の Google Sheets ID  | 1ABC...XYZ                       |

### 5.2 ローカル開発環境

**ローカルでのテスト実行**:

1. `.env.example` をコピーして `.env` を作成
2. `.env` ファイルに実際の認証情報を設定
3. `python src/main.py` で実行

**注意**: `.env` ファイルは `.gitignore` に含まれているため、GitHubにコミットされません。

### 5.3 ID 取得方法

**Spotify Playlist ID**:

- URL: `https://open.spotify.com/playlist/[ここがID]`

**Google Spreadsheet ID**:

- URL: `https://docs.google.com/spreadsheets/d/[ここがID]/edit`

## 6. ファイル構成

```
spotify-to-sheets/
├── .github/
│   └── workflows/
│       └── sync.yml         # GitHub Actions設定
├── src/
│   └── main.py             # メインスクリプト
├── .env.example            # 環境変数テンプレート
├── requirements.txt        # 依存パッケージ
└── README.md              # セットアップ手順
```

## 7. GitHub Actions 設定

```yaml
name: Spotify to Sheets Sync

on:
  schedule:
    - cron: "*/15 * * * *" # 15分ごと（UTC）
  workflow_dispatch: # 手動実行用

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      - run: pip install -r requirements.txt
      - run: python src/main.py
        env:
          SPOTIFY_CLIENT_ID: ${{ secrets.SPOTIFY_CLIENT_ID }}
          SPOTIFY_CLIENT_SECRET: ${{ secrets.SPOTIFY_CLIENT_SECRET }}
          GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
          SPOTIFY_PLAYLIST_ID: ${{ secrets.SPOTIFY_PLAYLIST_ID }}
          GOOGLE_SPREADSHEET_ID: ${{ secrets.GOOGLE_SPREADSHEET_ID }}
```

## 8. 依存パッケージ

```txt
spotipy==2.23.0
gspread==5.12.0
google-auth==2.25.0
python-dotenv==1.0.0
black===23.9.1
flake8===6.1.0
isort==5.12.0
```

## 9. エラーハンドリング

### 9.1 想定されるエラー

- Spotify API レート制限
- Google Sheets API クォータ超過
- ネットワークエラー
- 認証エラー

### 9.2 対処方法

- 分かりやすいエラーメッセージ（プレイリストIDエラーなど）
- エラーログ出力
- ローカル開発用 .env ファイルサポート

## 10. 処理フロー

```
1. 環境変数から認証情報を取得
2. Spotify APIに接続・認証
3. 指定プレイリストから全曲情報を取得
4. Google Sheetsに接続・認証
5. シートから既存データを取得
6. 重複チェック（アーティスト名+曲名）
7. 新規曲のみをリスト化
8. 新規曲をシートに追加（追加日付きで）
9. 処理結果をログ出力
```

## 11. ログ出力例

```
[2024/01/20 09:00:00] Starting sync...
[2024/01/20 09:00:01] Connected to Spotify API
[2024/01/20 09:00:02] Fetched 150 tracks from playlist
[2024/01/20 09:00:03] Connected to Google Sheets
[2024/01/20 09:00:04] Found 148 existing tracks
[2024/01/20 09:00:05] Adding 2 new tracks
[2024/01/20 09:00:06] Sync completed successfully
```

## 12. 制限事項

- 1 プレイリストあたり最大 10,000 曲まで対応
- Google Sheets 1 シートあたり最大 1,000 万セルまで
- 実行時間は最大 10 分（GitHub Actions 制限）

### 12.1 GitHub Actions 実行時間制限

- **Public リポジトリ**: 無制限（現在の設定: 15分間隔で実行可能）
- **Private リポジトリ**: 月間実行時間に制限あり
  - 15分間隔の頻繁な実行では制限に達する可能性
  - Private化する場合は実行間隔の調整が必要（例: 6時間ごと、1日1回など）
  - 最新の制限については GitHub の料金ページを確認

## 13. セキュリティ考慮事項

- 認証情報は GitHub Secrets で管理（コードに含めない）
- Service Account は最小権限の原則
- ログに認証情報を出力しない

---

この仕様書に基づいて実装を行う。質問や変更要望があれば実装前に確認すること。
