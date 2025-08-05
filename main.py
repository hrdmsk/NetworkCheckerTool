import eel
import dns.resolver
import socket # ポート接続確認のために標準ライブラリをインポート

# Eelを初期化
eel.init('web')

@eel.expose
def nslookup_py(domain, server):
    """ JavaScriptから呼び出されるNSLOOKUP処理 """
    if not domain:
        return "エラー: ドメイン名を入力してください。"
    output = []
    resolver = dns.resolver.Resolver()
    if server:
        try:
            resolver.nameservers = [server]
            output.append(f"DNSサーバー: {server}")
        except Exception as e:
            return f"エラー: 無効なDNSサーバーです。\n{e}"
    else:
        output.append("DNSサーバー: システムのデフォルト設定")
    output.append("----------------------------------------\n")
    # 問い合わせるレコードタイプのリスト
    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'CAA', 'DS', 'DNSKEY']
    for r_type in record_types:
        try:
            output.append(f"--- {r_type}レコード: {domain} ---")
            answers = resolver.resolve(domain, r_type)
            for rdata in answers:
                output.append(str(rdata))
        except dns.resolver.NoAnswer:
            output.append("レコードが見つかりませんでした。")
        except dns.resolver.NXDOMAIN:
            output.append("エラー: ドメインが存在しません。")
            break
        except Exception as e:
            output.append(f"クエリに失敗しました: {e}")
        finally:
            output.append("")
    return "\n".join(output)

@eel.expose
def test_port_connection_py(host, port_str):
    """
    指定されたホストとポートにTCP接続を試みる関数
    """
    if not host or not port_str:
        return "エラー: ホストとポート番号の両方を入力してください。"

    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise ValueError("ポート番号は1から65535の間でなければなりません。")
    except ValueError as e:
        return f"エラー: 無効なポート番号です。\n{e}"

    try:
        # タイムアウトを5秒に設定して接続を試みる
        with socket.create_connection((host, port), timeout=5) as sock:
            # 接続に成功した場合
            local_ip, local_port = sock.getsockname()
            remote_ip, remote_port = sock.getpeername()
            
            return (
                f"✅ 成功: {host} ({remote_ip}) のポート {port} に接続できました。\n\n"
                f"ローカルアドレス: {local_ip}:{local_port}\n"
                f"リモートアドレス: {remote_ip}:{remote_port}"
            )

    except socket.timeout:
        return f"❌ 失敗: タイムアウトしました。ホストが応答しないか、ファイアウォールによってブロックされている可能性があります。"
    except ConnectionRefusedError:
        return f"❌ 失敗: 接続が拒否されました。ホストはアクティブですが、ポートでリッスンしているサービスがありません。"
    except socket.gaierror:
        return f"❌ 失敗: ホスト名 '{host}' を解決できませんでした。ホスト名が正しいか確認してください。"
    except Exception as e:
        return f"❌ 失敗: 予期せぬエラーが発生しました。\n{type(e).__name__}: {e}"


# アプリケーションを開始
print("アプリケーションを起動しています...")
# 【修正点】使用するポートを8080番に変更
eel.start('index.html', size=(700, 750), port=8080)
print("アプリケーションを終了しました。")
