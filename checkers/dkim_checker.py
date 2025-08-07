# dkim_checker.py
import os
import sys
import json
import asyncio
import aiodns
import random

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

async def _query_dkim(resolver, selector, domain):
    """単一のDKIMセレクタを非同期で問い合わせる"""
    query_domain = f'{selector}._domainkey.{domain}'
    try:
        answers = await resolver.query(query_domain, 'TXT')
        for rdata in answers:
            if 'v=dkim1' in rdata.text.lower():
                return {'query': query_domain, 'records': [rdata.text]}
    except aiodns.error.DNSError:
        pass
    except Exception as e:
        if not isinstance(e, asyncio.TimeoutError):
            print(f"Query Error for {query_domain}: {e}")
    return None

async def find_dkim_record_async(domain, dkim_selector="", progress_callback=None, dns_servers=None):
    """
    DKIMレコードを非同期で検索する。
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

    resolvers = []
    if dns_servers and isinstance(dns_servers, list):
        random.shuffle(dns_servers)
        for server_ip in dns_servers:
            try:
                resolvers.append(aiodns.DNSResolver(nameservers=[server_ip]))
            except Exception as e:
                print(f"WARNING: Could not create resolver for {server_ip}: {e}")
    
    if not resolvers:
        resolvers.append(aiodns.DNSResolver())

    resolver_count = len(resolvers)
    print(f"INFO: Using a pool of {resolver_count} DNS resolvers for DKIM check.")

    tasks = []
    for i, selector in enumerate(selectors_to_check):
        resolver = resolvers[i % resolver_count]
        tasks.append(asyncio.create_task(_query_dkim(resolver, selector, domain)))
    
    done_count = 0
    for future in asyncio.as_completed(tasks):
        result = await future
        done_count += 1
        if progress_callback:
            progress_callback(done_count, total_selectors)
            
        if result:
            dkim_data = result
            print("INFO: Record found. Cancelling remaining tasks...")
            for task in tasks:
                if not task.done():
                    task.cancel()
            break

    await asyncio.gather(*tasks, return_exceptions=True)

    if not dkim_data.get('records'):
        dkim_data['status'] = "セレクタ候補ではDKIMレコードが見つかりませんでした。"

    return dkim_data, checked_selectors_list
