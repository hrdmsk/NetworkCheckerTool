# whois_checker.py
import socket
import json
import urllib.request # 標準のHTTPライブラリを使用

def _format_rdap_json(data):
    """受け取ったJSONデータを人間が読みやすい形式の文字列に整形する"""
    try:
        parsed_json = json.loads(data)
        return json.dumps(parsed_json, indent=4, ensure_ascii=False)
    except json.JSONDecodeError:
        return data

def _query_whois(server, query):
    """指定されたサーバーにWhoisクエリを送信し、応答を取得します。"""
    try:
        with socket.create_connection((server, 43), timeout=10) as sock:
            sock.sendall(query)
            response_bytes = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response_bytes += data
            return response_bytes.decode("utf-8", errors="ignore")
    except socket.error as e:
        return f"Error: Failed to connect to {server}. {e}"

def _get_whois_server(domain):
    """ドメインのWhoisサーバーをiana.orgに問い合わせて特定します。"""
    response_iana = _query_whois("whois.iana.org", f"{domain}\r\n".encode("utf-8"))
    for line in response_iana.splitlines():
        if line.strip().startswith("whois:"):
            return line.split(":", 1)[1].strip()
    return None

def _query_rdap(domain):
    """ドメインのRDAP情報を取得します (urllib.request版)"""
    tld = domain.split('.')[-1].lower()
    bootstrap_url = f"https://rdap.iana.org/domain/{tld}" # IANAのエンドポイントを使用
    
    try:
        # 1. IANAに問い合わせて、権威RDAPサーバーのURLを取得
        with urllib.request.urlopen(bootstrap_url) as response:
            if response.status != 200:
                return f"Error: IANA bootstrap failed with status {response.status}"
            bootstrap_data = json.loads(response.read())
        
        # linksの中からRDAPサーバーのベースURLを探す
        rdap_base_url = None
        if 'links' in bootstrap_data:
            for link in bootstrap_data['links']:
                if link.get('rel') == 'related' and 'href' in link:
                    rdap_base_url = link['href']
                    break
        
        if not rdap_base_url:
            return f"Error: No RDAP URL found for .{tld} in IANA response"

        # 2. 取得したURLを使って、実際のRDAPサーバーに問い合わせ
        if not rdap_base_url.endswith('/'):
            rdap_base_url += '/'
        
        final_rdap_url = f"{rdap_base_url}domain/{domain}"
        
        req = urllib.request.Request(
            final_rdap_url,
            headers={'Accept': 'application/rdap+json'}
        )

        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                return f"Error: RDAP server failed with status {response.status}"
            return response.read().decode('utf-8', 'ignore')

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"RDAP Error: {domain} not found on the server."
        return f"Error: RDAP HTTP query failed. Code: {e.code}, Reason: {e.reason}"
    except Exception as e:
        return f"Error: RDAP query failed. {e}"

def get_whois_info(domain):
    """
    まずRDAPで問い合わせ、失敗したら従来のWhoisにフォールバックします。
    """
    print(f"INFO: Performing RDAP lookup for {domain}...")
    rdap_info = _query_rdap(domain)
    
    if rdap_info and rdap_info.strip().startswith('{'):
        print("INFO: RDAP lookup successful.")
        return _format_rdap_json(rdap_info)
    
    print(f"INFO: RDAP failed or not supported, falling back to legacy Whois.")
    print(f"(RDAP message: {rdap_info})")
    
    whois_server = _get_whois_server(domain)
    if not whois_server:
        return f"Error: {domain} のWhoisサーバーを特定できませんでした。"

    print(f"INFO: Performing legacy Whois lookup via {whois_server}...")
    return _query_whois(whois_server, f"{domain}\r\n".encode("utf-8"))
