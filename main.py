import eel            # GUIを作成し、PythonとJavaScriptを連携させるためのライブラリ
import dns.resolver   # NSLOOKUP機能（DNSクエリ）を実行するためのライブラリ
import socket         # ポート接続確認やホスト名の解決など、低レベルなネットワーク通信を行うためのライブラリ
import sys            # アプリケーションの終了(sys.exit)や、EXE化された際のパス解決に使用
import subprocess     # pingやtracertなどのOSコマンドを実行するためのモジュール
import locale         # OSの標準文字コードを取得し、コマンド結果の文字化けを防ぐために使用
import json           # DNSサーバーのリストを記述したJSONファイルを読み込むために使用
import os             # ファイルパスを解決するためにインポート
import time           # 処理を一時停止(sleep)するために使用
import win32gui       # WindowsのGUIウィンドウを操作するためのライブラリ
import win32con       # win32guiで使う定数を定義したモジュール

def resource_path(relative_path):
    """
    EXE化された場合と、スクリプト実行の場合の両方で
    リソースへの正しいパスを取得します。
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Eelを初期化
eel.init('web')

# ウィンドウハンドルを格納するためのグローバル変数
hwnd = 0

@eel.expose
def set_always_on_top(is_top):
    """ ウィンドウを最前面に表示、または解除する """
    global hwnd
    if hwnd == 0:
        print("ウィンドウハンドルが見つかりません。")
        return

    try:
        if is_top:
            # 最前面に設定
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            print("ウィンドウを最前面に設定しました。")
        else:
            # 最前面を解除
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            print("ウィンドウの最前面表示を解除しました。")
    except Exception as e:
        print(f"ウィンドウの最前面設定中にエラーが発生しました: {e}")


@eel.expose
def get_dns_servers():
    """ web/dns_servers.jsonを読み込んで、サーバーのリストを返す """
    json_path = resource_path('web/dns_servers.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

@eel.expose
def nslookup_py(domain, server):
    if not domain:
        return {'error': "ドメイン名を入力してください。"}
    results = []
    resolver = dns.resolver.Resolver()
    if server:
        try:
            server_ip = socket.gethostbyname(server)
            resolver.nameservers = [server_ip]
        except socket.gaierror:
            return {'error': f"DNSサーバーのホスト名 '{server}' を解決できませんでした。"}
        except Exception as e:
            return {'error': f"無効なDNSサーバーです。\n{e}"}
    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'CAA', 'DS', 'DNSKEY']
    for r_type in record_types:
        record_data = {'type': r_type, 'records': []}
        try:
            answers = resolver.resolve(domain, r_type)
            for rdata in answers:
                record_data['records'].append(str(rdata))
            if not record_data['records']:
                record_data['status'] = "レコードが見つかりませんでした。"
        except dns.resolver.NoAnswer:
            record_data['status'] = "レコードが見つかりませんでした。"
        except dns.resolver.NXDOMAIN:
            return {'error': f"ドメイン '{domain}' が存在しません。"}
        except Exception as e:
            record_data['status'] = f"クエリ失敗: {e}"
        results.append(record_data)
    return results

@eel.expose
def test_port_connection_py(host, port_str):
    if not host or not port_str:
        return "エラー: ホストとポート番号の両方を入力してください。"
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise ValueError("ポート番号は1から65535の間でなければなりません。")
    except ValueError as e:
        return f"エラー: 無効なポート番号です。\n{e}"
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            local_ip, local_port = sock.getsockname()
            remote_ip, remote_port = sock.getpeername()
            return (
                f"✅ 成功: {host} ({remote_ip}) のポート {port} に接続できました。\n\n"
                f"ローカルアドレス: {local_ip}:{local_port}\n"
                f"リモートアドレス: {remote_ip}:{remote_port}"
            )
    except socket.timeout:
        return f"❌ 失敗: タイムアウトしました。"
    except ConnectionRefusedError:
        return f"❌ 失敗: 接続が拒否されました。"
    except socket.gaierror:
        return f"❌ 失敗: ホスト名 '{host}' を解決できませんでした。"
    except Exception as e:
        return f"❌ 失敗: 予期せぬエラーが発生しました。\n{type(e).__name__}: {e}"

def run_command(command):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=locale.getpreferredencoding(),
            errors='ignore',
            startupinfo=startupinfo
        )
        return result.stdout or result.stderr
    except FileNotFoundError:
        return f"エラー: '{command[0]}' コマンドが見つかりません。PATHが通っているか確認してください。"
    except Exception as e:
        return f"コマンド実行中にエラーが発生しました: {e}"

@eel.expose
def ping_py(host):
    if not host:
        return "エラー: ホストを入力してください。"
    command = ['ping', '-n', '4', host]
    return run_command(command)

@eel.expose
def traceroute_py(host):
    if not host:
        return "エラー: ホストを入力してください。"
    command = ['tracert', host]
    return run_command(command)

def close_callback(route, websockets):
    if not websockets:
        print('ブラウザが閉じられました。アプリケーションを終了します。')
        sys.exit()

print("アプリケーションを起動しています...")
# block=Falseで非ブロッキングモードで開始
eel.start('index.html', size=(700, 750), port=8080, close_callback=close_callback, block=False)

# ウィンドウハンドルを取得し、デフォルトで最前面に設定
# ウィンドウが表示されるまで最大5秒待つ
start_time = time.time()
while hwnd == 0 and time.time() - start_time < 5:
    hwnd = win32gui.FindWindow(None, "レンタルサーバ簡易確認ツール")
    time.sleep(0.1)

if hwnd:
    print(f"ウィンドウハンドルを取得しました: {hwnd}")
    set_always_on_top(True) # デフォルトで最前面に
else:
    print("警告: ウィンドウハンドルを取得できませんでした。最前面表示機能は無効です。")

# メインプロセスを維持するためのループ
while True:
    eel.sleep(1.0)
