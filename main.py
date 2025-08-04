import eel
import dns.resolver

# Eelを初期化し、UIファイルが置かれている'web'フォルダを指定します。
eel.init('web')

@eel.expose  # このデコレータにより、JavaScriptからこの関数を呼び出せるようになります。
def nslookup_py(domain, server):
    """
    JavaScriptから呼び出されるNSLOOKUP処理。
    ドメイン名とDNSサーバーを受け取り、結果を文字列で返します。
    """
    if not domain:
        return "エラー: ドメイン名を入力してください。"

    # 結果を格納するためのリスト
    output = []
    
    # DNSリゾルバーのインスタンスを作成
    resolver = dns.resolver.Resolver()
    
    # DNSサーバーが指定されている場合
    if server:
        try:
            # リゾルバーが使用するDNSサーバーを設定
            resolver.nameservers = [server]
            output.append(f"DNSサーバー: {server}")
        except Exception as e:
            # 設定に失敗した場合
            return f"エラー: 無効なDNSサーバーです。\n{e}"
    else:
        # 指定されていない場合はシステムのデフォルト設定を使用
        output.append("DNSサーバー: システムのデフォルト設定")
    
    output.append("----------------------------------------\n")
    
    # 問い合わせるレコードタイプのリスト
    record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'CAA', 'DS', 'DNSKEY']

    # 各レコードタイプについて順番に問い合わせを実行
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
            # ドメインが存在しない場合は以降の検索を中断
            break
        except Exception as e:
            output.append(f"クエリに失敗しました: {e}")
        finally:
            # 各レコードタイプの結果の後に改行を入れる
            output.append("") 

    # リストの各要素を改行で連結して一つの文字列として返す
    return "\n".join(output)

# アプリケーションのウィンドウを開始
# 'index.html' を表示し、ウィンドウサイズを指定します。
print("アプリケーションを起動しています...")
eel.start('index.html', size=(700, 700))
print("アプリケーションを終了しました。")

