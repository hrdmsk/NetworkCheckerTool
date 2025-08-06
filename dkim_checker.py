# dkim_checker.py
import os
import sys
import json
from datetime import datetime, timedelta
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

def _generate_full_historical_selectors(start_date=datetime(2015, 1, 1), check_yyyymmdd=False, check_rs_yyyymmdd=False):
    """
    指定された開始日から今日まで、毎日セレクタを生成します。
    """
    selectors = []
    end_date = datetime.utcnow()
    current_date = end_date
    delta = timedelta(days=1)
    while current_date >= start_date:
        date_str = current_date.strftime('%Y%m%d')
        if check_yyyymmdd:
            selectors.append(date_str)
        if check_rs_yyyymmdd:
            selectors.append(f"rs{date_str}")
        current_date -= delta
    return selectors


async def _query_dkim(resolver, selector, domain, cancel_event):
    """単一のDKIMセレクタを非同期で問い合わせる"""
    if cancel_event and cancel_event.is_set():
        return None
    
    query_domain = f'{selector}._domainkey.{domain}'
    try:
        answers = await resolver.query(query_domain, 'TXT')
        for rdata in answers:
            if 'v=dkim1' in rdata.text.lower():
                return {'query': query_domain, 'records': [rdata.text]}
    except aiodns.error.DNSError:
        pass
    except Exception as e:
        print(f"Query Error for {query_domain}: {e}")
    return None

async def find_dkim_record_async(domain, dkim_selector="", progress_callback=None, cancel_event=None, dns_servers=None, perform_yyyymmdd_check=False, perform_rs_yyyymmdd_check=False):
    """
    DKIMレコードを非同期で、複数のDNSサーバーに分散して検索する。
    """
    dkim_data = {'records': []}
    
    if dkim_selector:
        selectors_to_check = [dkim_selector]
    else:
        json_selectors = _load_dkim_selectors()
        if perform_yyyymmdd_check or perform_rs_yyyymmdd_check:
            print("INFO: Historical check enabled. Generating selectors...")
            historical_selectors = _generate_full_historical_selectors(
                start_date=datetime(2015, 1, 1),
                check_yyyymmdd=perform_yyyymmdd_check,
                check_rs_yyyymmdd=perform_rs_yyyymmdd_check
            )
            selectors_to_check = list(dict.fromkeys(historical_selectors + json_selectors))
        else:
            selectors_to_check = json_selectors
    
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

    semaphore = asyncio.Semaphore(100)

    async def wrapped_query(selector):
        async with semaphore:
            resolver = resolvers[random.randint(0, resolver_count - 1)]
            return await _query_dkim(resolver, selector, domain, cancel_event)

    tasks = [asyncio.create_task(wrapped_query(s)) for s in selectors_to_check]
    
    done_count = 0
    for future in asyncio.as_completed(tasks):
        if cancel_event and cancel_event.is_set():
            break
        
        result = await future
        done_count += 1
        if progress_callback:
            progress_callback(done_count, total_selectors)
            
        if result:
            dkim_data = result
            print("INFO: Record found. Cancelling remaining tasks...")
            cancel_event.set()
            break

    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    if cancel_event and cancel_event.is_set() and not dkim_data.get('records'):
        dkim_data['status'] = "ユーザーによってキャンセルされました。"
    elif not dkim_data.get('records'):
        dkim_data['status'] = "セレクタ候補ではDKIMレコードが見つかりませんでした。"

    return dkim_data, checked_selectors_list
