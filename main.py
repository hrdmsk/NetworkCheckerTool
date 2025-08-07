import webview
import dns.resolver
import socket
import sys
import subprocess
import locale
import whois_checker
import dkim_checker
import threading
import asyncio
import json
import os
from datetime import datetime

# windowオブジェクトをグローバル変数として宣言
window = None

# --- APIクラス: JavaScriptから呼び出す関数をここにまとめる ---
class Api:
    def __init__(self):
        self.dkim_cancel_event = threading.Event()
        self.dkim_thread = None

    def toggle_on_top(self, is_on_top):
        """
        ウィンドウの最前面表示を切り替える関数
        UIがフリーズしないように、安全な方法でウィンドウの状態を変更する
        """
        global window
        if window:
            # Timerを使って、現在の処理とは別のスレッドでウィンドウの状態を変更し、フリーズを防ぐ
            threading.Timer(0.01, lambda: setattr(window, 'on_top', is_on_top)).start()

    def nslookup_py(self, domain, server):
        if not domain: return {'error': "ドメイン名を入力してください。"}
        results = []
        resolver = dns.resolver.Resolver()
        if server:
            try:
                server_ip = socket.gethostbyname(server)
                resolver.nameservers = [server_ip]
            except Exception as e: return {'error': f"DNSサーバー '{server}' を解決できませんでした: {e}"}
        
        record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'CAA', 'DS', 'DNSKEY']
        for r_type in record_types:
            record_data = {'type': r_type, 'records': []}
            try:
                answers = resolver.resolve(domain, r_type)
                for rdata in answers:
                    if r_type == 'CNAME':
                        target = rdata.target.to_text().strip('.')
                        ip_string = self._get_ip_string(target, resolver)
                        record_data['records'].append(f"{target}{ip_string}")
                    elif r_type == 'MX':
                        target = rdata.exchange.to_text().strip('.')
                        ip_string = self._get_ip_string(target, resolver)
                        record_data['records'].append(f"{rdata.preference} {target}{ip_string}")
                    elif r_type == 'NS':
                        target = rdata.target.to_text().strip('.')
                        ip_string = self._get_ip_string(target, resolver)
                        record_data['records'].append(f"{target}{ip_string}")
                    else:
                        record_data['records'].append(str(rdata))
            except Exception as e:
                record_data['status'] = f"クエリ失敗: {e}"
            results.append(record_data)
        return results

    def _get_ip_string(self, hostname, resolver):
        ips = []
        try:
            a_answers = resolver.resolve(hostname, 'A')
            for rdata in a_answers: ips.append(f"A: {rdata}")
        except Exception: pass
        try:
            aaaa_answers = resolver.resolve(hostname, 'AAAA')
            for rdata in aaaa_answers: ips.append(f"AAAA: {rdata}")
        except Exception: pass
        return f" ({', '.join(ips)})" if ips else ""

    def test_port_connection_py(self, host, port_str):
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

    def _run_command(self, command):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            result = subprocess.run(command, capture_output=True, text=True, encoding=locale.getpreferredencoding(), errors='ignore', startupinfo=startupinfo)
            return result.stdout or result.stderr
        except Exception as e: return f"コマンド実行中にエラーが発生しました: {e}"

    def ping_py(self, host):
        if not host: return "エラー: ホストを入力してください。"
        return self._run_command(['ping', '-n', '4', host])

    def traceroute_py(self, host):
        if not host: return "エラー: ホストを入力してください。"
        return self._run_command(['tracert', host])

    def whois_py(self, query):
        if not query: return "エラー: ドメイン名またはIPアドレスを入力してください。"
        return whois_checker.get_whois_info(query)

    def check_email_auth_py(self, domain, dkim_selector):
        if self.dkim_thread and self.dkim_thread.is_alive():
            print("INFO: Previous DKIM check is running. Cancelling it...")
            self.dkim_cancel_event.set()
            self.dkim_thread.join()
        
        self.dkim_cancel_event.clear()
        self.dkim_thread = threading.Thread(target=self._run_auth_check, args=(domain, dkim_selector))
        self.dkim_thread.start()
        return {'status': 'started'}

    def _run_auth_check(self, domain, dkim_selector):
        global window
        try:
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

            public_dns_list = self._get_public_dns_servers()
            if public_dns_list is None:
                dkim_data = {'type': 'DKIM', 'status': "エラー: dns_servers.jsonが読み込めませんでした。"}
                results.append(dkim_data)
                if window:
                    window.evaluate_js(f'finish_auth_check({json.dumps({"results": results, "checked_selectors": []})})')
                return

            def update_progress(done, total):
                if window:
                    window.evaluate_js(f'update_dkim_progress({done}, {total})')

            dkim_result, checked_selectors = asyncio.run(
                dkim_checker.find_dkim_record_async(
                    domain, dkim_selector,
                    progress_callback=update_progress,
                    dns_servers=public_dns_list
                )
            )
            
            dkim_data = {'type': 'DKIM'}
            dkim_data.update(dkim_result)
            results.append(dkim_data)
            
            final_result = {'results': results, 'checked_selectors': checked_selectors}
            if window:
                window.evaluate_js(f'finish_auth_check({json.dumps(final_result)})')

        except Exception as e:
            print(f"ERROR in auth check thread: {e}")
            if window:
                window.evaluate_js(f'finish_auth_check({json.dumps({"error": str(e)})})')
    
    def _get_public_dns_servers(self):
        try:
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.'
            file_path = os.path.join(base_path, 'web', 'dns', 'dns_servers.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [server['ip'] for server in data.get('public', []) if server.get('ip')]
        except Exception: return None

# --- アプリケーションの起動 ---
if __name__ == '__main__':
    api = Api()
    window = webview.create_window(
        'レンタルサーバ確認ツール',
        'web/index.html',
        js_api=api,
        width=800,
        height=700
    )
    webview.start()
