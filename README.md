# Spotify to Google Sheets 同期システム

SpotifyのプレイリストをGoogle Sheetsに自動同期するPythonスクリプト。GitHub Actionsで6時間ごとに定期実行されます。

## 機能

- Spotifyの指定プレイリストから曲情報を取得
- Google Sheetsに差分データのみ追加（重複排除）
- 既存データ（ユーザーのメモ含む）は保持
- 削除された曲もシート上に残す（履歴として）
- GitHub Actionsで6時間ごとに自動実行
- 手動実行も可能

## セットアップ

### 1. 環境設定

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. ローカル開発用環境変数の設定

ローカルでテスト実行する場合は、`.env`ファイルを作成して認証情報を設定してください：

```sh
cp .env.example .env
```

`.env`ファイルを編集して実際の値を設定：

```sh
# Spotify API設定
SPOTIFY_CLIENT_ID=your_actual_client_id
SPOTIFY_CLIENT_SECRET=your_actual_client_secret
SPOTIFY_PLAYLIST_ID=your_actual_playlist_id

# Google Sheets API設定
GOOGLE_CREDENTIALS={"type": "service_account", "project_id": "your-project", ...}
GOOGLE_SPREADSHEET_ID=your_actual_spreadsheet_id
```

**注意**: `.env`ファイルは`.gitignore`に含まれているため、GitHubにはコミットされません。

### 3. Spotify App の作成

1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) にアクセス
2. 新しいアプリを作成
3. Client IDとClient Secretを取得

### 4. Google Service Account の作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを作成または選択
3. Google Sheets APIを有効化
4. Service Accountを作成し、JSON形式の認証情報をダウンロード

### 5. GitHub Secrets の設定

以下のSecretsをGitHubリポジトリに設定してください：

| Secret名 | 説明 | 例 |
|----------|------|-----|
| `SPOTIFY_CLIENT_ID` | Spotify AppのClient ID | `1234567890abcdef...` |
| `SPOTIFY_CLIENT_SECRET` | Spotify AppのClient Secret | `abcdef1234567890...` |
| `GOOGLE_CREDENTIALS` | Service AccountのJSON全体 | `{"type": "service_account", ...}` |
| `SPOTIFY_PLAYLIST_ID` | 対象のSpotifyプレイリストID | `37i9dQZF1DXcBWIGoYBM5M` |
| `GOOGLE_SPREADSHEET_ID` | 書き込み先のGoogle SheetsID | `1ABC...XYZ` |

### 6. ID取得方法

**Spotify Playlist ID**:
- URL: `https://open.spotify.com/playlist/[ここがID]`

**Google Spreadsheet ID**:
- URL: `https://docs.google.com/spreadsheets/d/[ここがID]/edit`

## 使用方法

### 手動実行

```sh
python src/main.py
```

### 自動実行

GitHub ActionsによりUTCで6時間ごと（0:00, 6:00, 12:00, 18:00）に自動実行されます。

### 手動でワークフローを実行

GitHubのActionsタブから「Spotify to Sheets Sync」ワークフローを選択し、「Run workflow」をクリックしてください。

## Google Sheetsのカラム構成

| カラム名 | 説明 | 自動/手動 |
|----------|------|-----------|
| アーティスト | アーティスト名（複数の場合は", "で結合） | 自動 |
| アルバム | アルバム名 | 自動 |
| 曲名 | トラック名 | 自動 |
| メモ | ユーザーが自由に記入するメモ欄 | 手動 |
| 追加日 | シートに追加された日付（YYYY/MM/DD形式） | 自動 |

## 開発

### コードフォーマット

```sh
python -m black src/main.py
flake8 src/main.py
```

### 一括フォーマット

```sh
sh format.sh
```

## 制限事項

- 1プレイリストあたり最大10,000曲まで対応
- Google Sheets 1シートあたり最大1,000万セルまで
- 実行時間は最大10分（GitHub Actions制限）

## トラブルシューティング

### よくあるエラー

1. **Spotify API認証エラー**: Client IDとClient Secretが正しく設定されているか確認
2. **Google Sheets API認証エラー**: Service Accountの認証情報とSpreadsheet IDが正しく設定されているか確認
3. **プレイリストが見つからない**: Spotify Playlist IDが正しく設定されているか確認
