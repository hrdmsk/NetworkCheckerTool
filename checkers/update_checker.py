# checkers/update_checker.py
import urllib.request

def _compare_versions(v1, v2):
    """バージョン文字列 (例: '1.0.10') を数値として正しく比較する"""
    parts1 = [int(p) for p in v1.split('.')]
    parts2 = [int(p) for p in v2.split('.')]
    return parts1 > parts2

def check(current_version, version_url, window):
    """
    指定されたURLから最新バージョンを取得し、現在のバージョンと比較します。
    新しいバージョンが見つかった場合、UIに通知を表示します。
    """
    try:
        if current_version == "N/A":
            return # ローカルバージョンが読めなければ何もしない

        print(f"INFO: Checking for updates from {version_url}")
        with urllib.request.urlopen(version_url, timeout=5) as response:
            if response.status == 200:
                latest_version = response.read().decode('utf-8').strip()
                print(f"INFO: Current version: {current_version}, Latest version: {latest_version}")
                
                # 数値としてバージョンを比較
                if _compare_versions(latest_version, current_version):
                    print(f"INFO: New version found: {latest_version}")
                    if window:
                        window.evaluate_js(f'show_update_notification("{latest_version}")')
    except Exception as e:
        print(f"ERROR: Failed to check for updates: {e}")