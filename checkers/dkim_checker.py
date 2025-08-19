# checkers/dkim_checker.py
import os
import sys
import json
import dns.resolver # 非同期から同期ライブラリへ

def _load_dkim_selectors(filename='dkim_selectors.json'):
    """
    JSONファイルからDKIMセレクタのリストを読み込む。
    """
    try:
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.'
        file_path = os.path.join(base_path, 'web', 'dns', filename)
        
        if not os.path.exists(file_path):
            print(f"WARNING: Selector file not found at '{file_path}'")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('selectors', [])
    except Exception as e:
        print(f"ERROR: Failed to load selector file: {e}")
        return []

def find_dkim_record(domain, dkim_selector="", progress_callback=None): # 関数名を変更
    """
    DKIMレコードを同期的に検索する。
    """
    dkim_data = {'records': []}
    
    if dkim_selector:
        selectors_to_check = [dkim_selector]
    else:
        selectors_to_check = _load_dkim_selectors()
    
    checked_selectors_list = list(selectors_to_check)
    total_selectors = len(selectors_to_check)
    if not selectors_to_check:
        dkim_data['status'] = "確認するDKIMセレクタがありませんでした。"
        return dkim_data, []

    resolver = dns.resolver.Resolver()
    
    # 一つずつ順番に問い合わせる
    for i, selector in enumerate(selectors_to_check):
        query_domain = f'{selector}._domainkey.{domain}'
        try:
            answers = resolver.resolve(query_domain, 'TXT')
            for rdata in answers:
                if 'v=dkim1' in rdata.to_text().lower():
                    dkim_data['query'] = query_domain
                    dkim_data['records'] = [rdata.to_text().strip('"')]
                    print("INFO: Record found. Stopping further checks.")
                    # 見つかった時点で終了
                    if progress_callback:
                        progress_callback(i + 1, total_selectors)
                    return dkim_data, checked_selectors_list
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass # 見つからないのは正常
        except Exception as e:
            print(f"Query Error for {query_domain}: {e}")

        if progress_callback:
            progress_callback(i + 1, total_selectors)

    if not dkim_data.get('records'):
        dkim_data['status'] = "セレクタ候補ではDKIMレコードが見つかりませんでした。"

    return dkim_data, checked_selectors_list
