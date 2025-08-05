import eel            # GUIを作成し、PythonとJavaScriptを連携させるためのライブラリ
import dns.resolver   # NSLOOKUP機能（DNSクエリ）を実行するためのライブラリ
import socket         # ポート接続確認やホスト名の解決など、低レベルなネットワーク通信を行うためのライブラリ
import sys            # アプリケーションの終了(sys.exit)に使用
import subprocess     # pingやtracertなどのOSコマンドを実行するためのモジュール
import locale         # OSの標準文字コードを取得し、コマンド結果の文字化けを防ぐために使用
import whois          # Whois情報を取得するためのライブラリ

# Eelを初期化
eel.init('web')

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

@eel.expose
def whois_py(query):
    if not query:
        return "エラー: ドメイン名またはIPアドレスを入力してください。"
    try:
        w = whois.whois(query)
        return w.text if hasattr(w, 'text') else str(w)
    except Exception as e:
        return f"Whois情報の取得中にエラーが発生しました:\n{e}"

@eel.expose
def check_email_auth_py(domain, dkim_selector):
    """ SPF, DKIM, DMARCレコードを検索して返す """
    if not domain:
        return {'error': "ドメイン名を入力してください。"}

    results = []
    resolver = dns.resolver.Resolver()

    # SPFレコードの検索
    spf_data = {'type': 'SPF', 'records': []}
    try:
        answers = resolver.resolve(domain, 'TXT')
        for rdata in answers:
            if 'v=spf1' in rdata.to_text().lower():
                spf_data['records'].append(rdata.to_text().strip('"'))
        if not spf_data['records']:
            spf_data['status'] = "SPFレコードが見つかりませんでした。"
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        spf_data['status'] = "SPFレコードが見つかりませんでした。"
    except Exception as e:
        spf_data['status'] = f"クエリ失敗: {e}"
    results.append(spf_data)

    # DMARCレコードの検索
    dmarc_data = {'type': 'DMARC', 'records': []}
    try:
        answers = resolver.resolve(f'_dmarc.{domain}', 'TXT')
        for rdata in answers:
            if 'v=dmarc1' in rdata.to_text().lower():
                dmarc_data['records'].append(rdata.to_text().strip('"'))
        if not dmarc_data['records']:
            dmarc_data['status'] = "DMARCレコードが見つかりませんでした。"
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        dmarc_data['status'] = "DMARCレコードが見つかりませんでした。"
    except Exception as e:
        dmarc_data['status'] = f"クエリ失敗: {e}"
    results.append(dmarc_data)

    # DKIMレコードの検索
    dkim_data = {'type': 'DKIM', 'records': []}
    
    # セレクタが指定されているかチェック
    if dkim_selector:
        selectors_to_check = [dkim_selector]
    else:
        # 指定されていない場合、一般的なセレクタのリストを使用
        selectors_to_check = ['google', 'default', 'selector1', 'selector2', 's1', 'k1']

    for selector in selectors_to_check:
        try:
            query_domain = f'{selector}._domainkey.{domain}'
            answers = resolver.resolve(query_domain, 'TXT')
            
            dkim_records_found = []
            for rdata in answers:
                if 'v=dkim1' in rdata.to_text().lower():
                    dkim_records_found.append(rdata.to_text().strip('"'))
            
            # レコードが見つかった場合
            if dkim_records_found:
                dkim_data['query'] = query_domain
                dkim_data['records'] = dkim_records_found
                break # 最初に見つかった時点でループを抜ける

        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            continue # 次のセレクタへ
        except Exception as e:
            dkim_data['status'] = f"クエリ失敗: {e}"
            break

    # ループが終了してもレコードが見つからなかった場合
    if not dkim_data['records'] and 'status' not in dkim_data:
        if dkim_selector:
             dkim_data['status'] = f"セレクタ '{dkim_selector}' でDKIMレコードが見つかりませんでした。"
        else:
             dkim_data['status'] = "一般的なセレクタではDKIMレコードが見つかりませんでした。"

    results.append(dkim_data)
    
    return results

def close_callback(route, websockets):
    if not websockets:
        print('ブラウザが閉じられました。アプリケーションを終了します。')
        sys.exit()

print("アプリケーションを起動しています...")
eel.start('index.html', size=(700, 800), port=8080, close_callback=close_callback)
print("アプリケーションを終了しました。")
