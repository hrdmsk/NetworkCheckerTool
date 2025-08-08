import dns.resolver
import sys
import threading
import json
import os

from checkers import whois_checker, dkim_checker, dns_checker, network_checker, update_checker
from logger_setup import log_execution

_window = None

def set_window_for_api(window):
    global _window
    _window = window

def _get_app_version():
    """version.txtから現在のアプリケーションバージョンを読み込む"""
    try:
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.'
        file_path = os.path.join(base_path, 'version.txt')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"ERROR: Could not read version.txt: {e}")
        return "N/A" 

class Api:
    def __init__(self):
        self.dkim_cancel_event = threading.Event()
        self.dkim_thread = None

    def get_app_version(self):
        """UIにバージョンを渡すための関数"""
        return _get_app_version()

    def check_for_updates(self, version_url):
        """アップデートチェックをバックグラウンドで開始する"""
        thread = threading.Thread(target=self._run_update_check, args=(version_url,))
        thread.start()

    def _run_update_check(self, version_url):
        """実際のアップデートチェック処理"""
        current_version = _get_app_version()
        # update_checkerライブラリを呼び出す
        update_checker.check(current_version, version_url, _window)

    def toggle_on_top(self, is_on_top):
        if _window:
            threading.Timer(0.01, lambda: setattr(_window, 'on_top', is_on_top)).start()

    # --- 各機能の呼び出し ---
    @log_execution
    def nslookup_py(self, domain, server):
        return dns_checker.nslookup(domain, server)
    @log_execution
    def test_port_connection_py(self, host, port_str):
        return network_checker.test_port_connection(host, port_str)
    @log_execution
    def ping_py(self, host):
        return network_checker.ping(host)
    @log_execution
    def traceroute_py(self, host):
        return network_checker.traceroute(host)
    @log_execution
    def whois_py(self, query):
        return whois_checker.get_whois_info(query)
    @log_execution
    def check_email_auth_py(self, domain, dkim_selector):
        thread = threading.Thread(target=self._run_auth_check, args=(domain, dkim_selector))
        thread.start()
        return {'status': 'started'}

    def _run_auth_check(self, domain, dkim_selector):
        try:
            results = []
            resolver = dns.resolver.Resolver()
            
            # SPF
            spf_data = {'type': 'SPF', 'records': []}
            try:
                answers = resolver.resolve(domain, 'TXT')
                for rdata in answers:
                    if 'v=spf1' in rdata.to_text().lower():
                        spf_data['records'].append(rdata.to_text().strip('"'))
                if not spf_data['records']: spf_data['status'] = "レコードが見つかりませんでした。"
            except Exception as e: spf_data['status'] = f"クエリ失敗: {e}"
            results.append(spf_data)

            # DMARC
            dmarc_data = {'type': 'DMARC', 'records': []}
            try:
                answers = resolver.resolve(f'_dmarc.{domain}', 'TXT')
                for rdata in answers:
                    if 'v=dmarc1' in rdata.to_text().lower():
                        dmarc_data['records'].append(rdata.to_text().strip('"'))
                if not dmarc_data['records']: dmarc_data['status'] = "DMARCレコードが見つかりませんでした。"
            except Exception as e: dmarc_data['status'] = f"クエリ失敗: {e}"
            results.append(dmarc_data)

            # DKIM
            public_dns_list = self._get_public_dns_servers()
            if public_dns_list is None:
                dkim_data = {'type': 'DKIM', 'status': "エラー: dns_servers.jsonが読み込めませんでした。"}
                results.append(dkim_data)
                if _window: _window.evaluate_js(f'finish_auth_check({json.dumps({"results": results, "checked_selectors": []})})')
                return

            def update_progress(done, total):
                if _window: _window.evaluate_js(f'update_dkim_progress({done}, {total})')

            # asyncio.run を削除し、同期関数を直接呼び出し
            dkim_result, checked_selectors = dkim_checker.find_dkim_record(
                domain, dkim_selector,
                progress_callback=update_progress
            )
            
            dkim_data = {'type': 'DKIM'}
            dkim_data.update(dkim_result)
            results.append(dkim_data)
            
            final_result = {'results': results, 'checked_selectors': checked_selectors}
            if _window: _window.evaluate_js(f'finish_auth_check({json.dumps(final_result)})')

        except Exception as e:
            print(f"ERROR in auth check thread: {e}")
            if _window: _window.evaluate_js(f'finish_auth_check({json.dumps({"error": str(e)})})')
    
    def _get_public_dns_servers(self):
        try:
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.'
            file_path = os.path.join(base_path, 'web', 'dns', 'dns_servers.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [server['ip'] for server in data.get('public', []) if server.get('ip')]
        except Exception: return None