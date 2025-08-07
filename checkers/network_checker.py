# checkers/network_checker.py
import socket
import subprocess
import locale

def _run_command(command):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        result = subprocess.run(command, capture_output=True, text=True, encoding=locale.getpreferredencoding(), errors='ignore', startupinfo=startupinfo)
        return result.stdout or result.stderr
    except Exception as e: return f"コマンド実行中にエラーが発生しました: {e}"

def test_port_connection(host, port_str):
    if not host or not port_str: return "エラー: ホストとポート番号の両方を入力してください。"
    try:
        port = int(port_str)
        if not (1 <= port <= 65535): raise ValueError("ポート番号は1から65535の間でなければなりません。")
    except ValueError as e: return f"エラー: 無効なポート番号です。\n{e}"
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            remote_ip = sock.getpeername()[0]
            return f"✅ 成功: {host} ({remote_ip}) のポート {port} に接続できました。"
    except Exception as e: return f"❌ 失敗: 予期せぬエラーが発生しました。\n{type(e).__name__}: {e}"

def ping(host):
    if not host: return "エラー: ホストを入力してください。"
    return _run_command(['ping', '-n', '4', host])

def traceroute(host):
    if not host: return "エラー: ホストを入力してください。"
    return _run_command(['tracert', host])
