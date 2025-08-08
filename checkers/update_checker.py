# checkers/update_checker.py
import urllib.request

def get_latest_version(version_url):
    """
    指定されたURLから最新のバージョン番号を取得します。
    成功した場合はバージョン文字列を、失敗した場合はNoneを返します。
    """
    try:
        print(f"INFO: Checking for updates from {version_url}")
        # タイムアウトを5秒に設定して、URLにアクセス
        with urllib.request.urlopen(version_url, timeout=5) as response:
            if response.status == 200:
                # 読み込んだ内容をUTF-8でデコードし、余分な空白を削除
                latest_version = response.read().decode('utf-8').strip()
                return latest_version
    except Exception as e:
        # エラーが発生した場合はログに記録
        print(f"ERROR: Failed to check for updates: {e}")
    
    # 失敗した場合はNoneを返す
    return None