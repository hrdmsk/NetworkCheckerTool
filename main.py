import eel
import dns.resolver
import socket
import sys
import subprocess
import locale
import whois
import dkim_checker
import threading
import asyncio
import json
import os
from datetime import datetime

# Eelを初期化
eel.init('web')

dkim_cancel_event = threading.Event()
dkim_thread = None # ★追加: 実行中のスレッドを管理する変数

def get_public_dns_servers():
    """
    dns_servers.jsonを読み込み、'public'カテゴリのIPアドレスリストを返す。
    読み込みに失敗した場合はNoneを返す。
    """
    try:
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.'
        file_path = os.path.join(base_path, 'web', 'dns', 'dns_servers.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [server['ip'] for server in data.get('public', []) if server.get('ip')]
    except Exception as e:
        print(f"ERROR: Could not read dns_servers.json: {e}")
        return None

@eel.expose
def nslookup_py(domain, server):
    """
    ドメインのDNSレコードを検索する。
    CNAME, MX, NSで見つかったホスト名のIPアドレスも解決し、同じ行に表示する。
    """
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
                if r_type == 'CNAME':
                    target = rdata.target.to_text().strip('.')
                    ip_string = _get_ip_string(target, resolver)
                    record_data['records'].append(f"{target}{ip_string}")
                elif r_type == 'MX':
                    target = rdata.exchange.to_text().strip('.')
                    ip_string = _get_ip_string(target, resolver)
                    record_data['records'].append(f"{rdata.preference} {target}{ip_string}")
                elif r_type == 'NS':
                    target = rdata.target.to_text().strip('.')
                    ip_string = _get_ip_string(target, resolver)
                    record_data['records'].append(f"{target}{ip_string}")
                else:
                    record_data['records'].append(str(rdata))

            if not record_data['records']:
                record_data['status'] = "レコードが見つかりませんでした。"
        except dns.resolver.NoAnswer:
            record_data['status'] = "レコードが見つかりませんでした。"
        except dns.resolver.NXDOMAIN:
            if not results: return {'error': f"ドメイン '{domain}' が存在しません。"}
            record_data['status'] = "レコードが見つかりませんでした。"
        except Exception as e:
            record_data['status'] = f"クエリ失敗: {e}"
        results.append(record_data)

    return results

def _get_ip_string(hostname, resolver):
    """
    指定されたホスト名のAおよびAAAAレコードを解決し、整形された文字列を返すヘルパー関数。
    """
    ips = []
    try:
        a_answers = resolver.resolve(hostname, 'A')
        for rdata in a_answers:
            ips.append(f"A: {rdata}")
    except Exception:
        pass
    try:
        aaaa_answers = resolver.resolve(hostname, 'AAAA')
        for rdata in aaaa_answers:
            ips.append(f"AAAA: {rdata}")
    except Exception:
        pass
    
    if ips:
        return f" ({', '.join(ips)})"
    return ""

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
            local_addr = sock.getsockname()
            remote_addr = sock.getpeername()
            
            local_ip = local_addr[0]
            local_port = local_addr[1]
            remote_ip = remote_addr[0]
            remote_port = remote_addr[1]
            
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
def check_email_auth_py(domain, dkim_selector, perform_yyyymmdd_check, perform_rs_yyyymmdd_check):
    """
    メール認証の確認を別スレッドで開始する。
    実行中の古いスレッドがあれば、キャンセルしてから新しいスレッドを開始する。
    """
    global dkim_thread
    
    # 既にスレッドが実行中であれば、キャンセルシグナルを送って終了を待つ
    if dkim_thread and dkim_thread.is_alive():
        print("INFO: Previous DKIM check is running. Cancelling it...")
        dkim_cancel_event.set()
        dkim_thread.join() # 古いスレッドが終了するのを待つ
        print("INFO: Previous DKIM check cancelled.")

    dkim_cancel_event.clear()
    dkim_thread = threading.Thread(target=run_auth_check, args=(domain, dkim_selector, perform_yyyymmdd_check, perform_rs_yyyymmdd_check))
    dkim_thread.start()
    return {'status': 'started'}

@eel.expose
def cancel_dkim_check():
    """フロントエンドからキャンセル指令を受け取る"""
    print("INFO: Received cancel signal from frontend.")
    dkim_cancel_event.set()

def summarize_selectors(selector_list):
    """確認したセレクタのリストを要約して文字列を返す"""
    if not selector_list:
        return ""

    date_selectors = []
    other_selectors = []
    
    for s in selector_list:
        clean_s = s[2:] if s.startswith('rs') else s
        if clean_s.isdigit() and len(clean_s) == 8:
            try:
                datetime.strptime(clean_s, '%Y%m%d')
                date_selectors.append(clean_s)
            except ValueError:
                other_selectors.append(s)
        else:
            other_selectors.append(s)
            
    summary_parts = []
    if date_selectors:
        date_selectors.sort()
        start_date = date_selectors[0]
        end_date = date_selectors[-1]
        summary_parts.append(f"日付セレクタ範囲: {start_date} ～ {end_date}")

    if other_selectors:
        summary_parts.append(f"その他: {', '.join(other_selectors)}")
        
    return " | ".join(summary_parts)

def run_auth_check(domain, dkim_selector, perform_yyyymmdd_check, perform_rs_yyyymmdd_check):
    """
    実際の認証チェック処理。この関数がバックグラウンドで動く。
    """
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
            spf_data['status'] = "レコードが見つかりませんでした。"
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
    except Exception as e:
        dmarc_data['status'] = f"クエリ失敗: {e}"
    results.append(dmarc_data)

    # DKIMの確認 (非同期処理)
    try:
        public_dns_list = get_public_dns_servers()
        if public_dns_list is None:
            dkim_data = {'type': 'DKIM', 'status': "エラー: dns_servers.jsonが読み込めませんでした。DKIMの確認を中止しました。"}
            results.append(dkim_data)
            eel.finish_auth_check({'results': results, 'checked_selectors_summary': ''})
            return

        def update_progress(done, total):
            eel.update_dkim_progress(done, total)

        dkim_result, checked_selectors = asyncio.run(
            dkim_checker.find_dkim_record_async(
                domain, 
                dkim_selector,
                progress_callback=update_progress,
                cancel_event=dkim_cancel_event,
                dns_servers=public_dns_list,
                perform_yyyymmdd_check=perform_yyyymmdd_check,
                perform_rs_yyyymmdd_check=perform_rs_yyyymmdd_check
            )
        )
        
        dkim_data = {'type': 'DKIM'}
        dkim_data.update(dkim_result)
        results.append(dkim_data)
        
        selector_summary = summarize_selectors(checked_selectors)
        eel.finish_auth_check({'results': results, 'checked_selectors_summary': selector_summary})

    except Exception as e:
        print(f"ERROR in auth check thread: {e}")
        eel.finish_auth_check({'error': str(e)})

def close_callback(route, websockets):
    if not websockets:
        print('ブラウザが閉じられました。アプリケーションを終了します。')
        sys.exit()

print("アプリケーションを起動しています...")
eel.start('index.html', size=(700, 800), port=8080, close_callback=close_callback)
print("アプリケーションを終了しました。")
