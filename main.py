import eel
import dns.resolver
import socket
import sys
import subprocess
import locale
import json # JSONファイルを扱うためにインポート

# Eelを初期化
eel.init('web')

@eel.expose
def get_dns_servers():
    """ web/dns_servers.jsonを読み込んで、サーバーのリストを返す """
    try:
        with open('web/dns_servers.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return [] # ファイルが見つからない場合は空のリストを返す
    except json.JSONDecodeError:
        return [] # JSONの形式が正しくない場合は空のリストを返す

@eel.expose
def nslookup_py(domain, server):
    """
    JavaScriptから呼び出されるNSLOOKUP処理。
    結果を構造化された辞書型のリストで返す。
    """
    if not domain:
        return {'error': "ドメイン名を入力してください。"}
    
    results = []
    resolver = dns.resolver.Resolver()
    
    # DNSサーバーの設定
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
    """ subprocessでコマンドを実行する共通関数 (Windows専用) """
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
    """ Pingを実行する (Windows専用) """
    if not host:
        return "エラー: ホストを入力してください。"
    command = ['ping', '-n', '4', host]
    return run_command(command)

@eel.expose
def traceroute_py(host):
    """ Tracerouteを実行する (Windows専用) """
    if not host:
        return "エラー: ホストを入力してください。"
    command = ['tracert', host]
    return run_command(command)

def close_callback(route, websockets):
    if not websockets:
        print('ブラウザが閉じられました。アプリケーションを終了します。')
        sys.exit()

print("アプリケーションを起動しています...")
eel.start('index.html', size=(700, 750), port=8080, close_callback=close_callback)
print("アプリケーションを終了しました。")
