import os
import json
from datetime import datetime
from typing import List, Dict, Set
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import gspread
from google.oauth2 import service_account

# .envファイルの読み込み（ローカル開発用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenvがインストールされていない場合は無視
    pass


class SpotifyToSheets:
    def __init__(self):
        self.spotify = None
        self.sheets_client = None
        self.spreadsheet = None
        self.worksheet = None

    def setup_spotify_client(self) -> None:
        """Spotify APIクライアントを初期化"""
        client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError("Spotify credentials not found in environment variables")

        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
        self.spotify = spotipy.Spotify(
            client_credentials_manager=client_credentials_manager
        )
        print(
            f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Connected to Spotify API"
        )

    def setup_sheets_client(self) -> None:
        """Google Sheets APIクライアントを初期化"""
        credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
        spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID")

        if not credentials_json or not spreadsheet_id:
            raise ValueError(
                "Google Sheets credentials not found in environment variables"
            )

        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )

        self.sheets_client = gspread.authorize(credentials)
        self.spreadsheet = self.sheets_client.open_by_key(spreadsheet_id)
        self.worksheet = self.spreadsheet.sheet1
        print(
            f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Connected to Google Sheets"
        )

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, str]]:
        """指定されたプレイリストから全曲情報を取得"""
        try:
            tracks = []
            results = self.spotify.playlist_tracks(playlist_id, limit=50)

            while results:
                for item in results["items"]:
                    if item["track"] and item["track"]["type"] == "track":
                        track = item["track"]
                        artists = ", ".join([artist["name"] for artist in track["artists"]])
                        tracks.append(
                            {
                                "アーティスト": artists,
                                "アルバム": track["album"]["name"],
                                "曲名": track["name"],
                            }
                        )

                if results["next"]:
                    results = self.spotify.next(results)
                else:
                    break

            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Fetched {len(tracks)} tracks from playlist"
            )
            return tracks
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                raise ValueError(
                    f"プレイリストが見つかりません。プレイリストID '{playlist_id}' が正しいか、"
                    f"プレイリストが公開されているか確認してください。"
                )
            else:
                raise

    def get_existing_tracks(self) -> Set[str]:
        """シートから既存の曲情報を取得（重複判定用）"""
        try:
            records = self.worksheet.get_all_records()
            existing_tracks = set()

            for record in records:
                if record.get("アーティスト") and record.get("曲名"):
                    unique_key = f"{record['アーティスト']}_{record['曲名']}"
                    existing_tracks.add(unique_key)

            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Found {len(existing_tracks)} existing tracks"
            )
            return existing_tracks
        except Exception as e:
            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Error reading existing tracks: {e}"
            )
            return set()

    def setup_sheet_headers(self) -> None:
        """シートのヘッダーを設定（初回のみ）"""
        try:
            if self.worksheet.row_count == 0 or not self.worksheet.get_all_values():
                headers = ["アーティスト", "アルバム", "曲名", "メモ", "追加日"]
                self.worksheet.append_row(headers)
                print(
                    f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Set up sheet headers"
                )
        except Exception as e:
            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Error setting up headers: {e}"
            )

    def add_new_tracks(self, new_tracks: List[Dict[str, str]]) -> None:
        """新規曲をシートに追加"""
        if not new_tracks:
            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] No new tracks to add"
            )
            return

        today = datetime.now().strftime("%Y/%m/%d")
        rows_to_add = []

        for track in new_tracks:
            row = [track["アーティスト"], track["アルバム"], track["曲名"], "", today]  # メモ欄は空白
            rows_to_add.append(row)

        try:
            self.worksheet.append_rows(rows_to_add)
            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Adding {len(new_tracks)} new tracks"
            )
        except Exception as e:
            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Error adding tracks: {e}"
            )
            raise

    def sync_playlist_to_sheets(self) -> None:
        """メイン処理：プレイリストをシートに同期"""
        try:
            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Starting sync..."
            )

            # 認証とAPI接続
            self.setup_spotify_client()
            self.setup_sheets_client()

            # シートのヘッダー設定
            self.setup_sheet_headers()

            # プレイリストIDの取得
            playlist_id = os.environ.get("SPOTIFY_PLAYLIST_ID")
            if not playlist_id:
                raise ValueError(
                    "Spotify playlist ID not found in environment variables"
                )

            # Spotifyからプレイリスト取得
            spotify_tracks = self.get_playlist_tracks(playlist_id)

            # 既存データ取得
            existing_tracks = self.get_existing_tracks()

            # 新規曲の特定
            new_tracks = []
            for track in spotify_tracks:
                unique_key = f"{track['アーティスト']}_{track['曲名']}"
                if unique_key not in existing_tracks:
                    new_tracks.append(track)

            # 新規曲を追加
            self.add_new_tracks(new_tracks)

            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Sync completed successfully"
            )

        except Exception as e:
            print(
                f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] Sync failed: {e}"
            )
            raise


def main():
    """メイン関数"""
    sync_tool = SpotifyToSheets()
    sync_tool.sync_playlist_to_sheets()


if __name__ == "__main__":
    main()
