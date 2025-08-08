# checkers/dns_checker.py
import dns.resolver
import socket

def _get_ip_string(hostname, resolver):
    """
    指定されたホスト名のAおよびAAAAレコードを解決し、改行された文字列を返す。
    """
    ips = []
    
    # Aレコード (IPv4)
    try:
        a_answers = resolver.resolve(hostname, 'A')
        for rdata in a_answers:
            ips.append(f"A: {rdata}")
    except Exception:
        pass
        
    # AAAAレコード (IPv6)
    try:
        aaaa_answers = resolver.resolve(hostname, 'AAAA')
        for rdata in aaaa_answers:
            ips.append(f"AAAA: {rdata}")
    except Exception:
        pass
    
    # 結果を改行して見やすく整形
    if ips:
        # 各IPの前にインデントと矢印を追加して、見やすくする
        return "\n    -> " + "\n    -> ".join(ips)
    return ""

def nslookup(domain, server):
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
        except Exception as e:
            record_data['status'] = f"クエリ失敗: {e}"
        results.append(record_data)
    return results
