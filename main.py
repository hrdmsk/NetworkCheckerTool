import webview
from api import Api, set_window_for_api # set_window_for_apiをインポート

# api.py内のバックグラウンド処理からUIを更新するために必要
window = None

if __name__ == '__main__':
    api = Api()
    window = webview.create_window(
        'レンタルサーバ確認ツール',
        'web/index.html',
        js_api=api,
        width=800,
        height=700,
        text_select=True
    )
    
    # api.pyにwindowオブジェクトを渡す
    set_window_for_api(window) 
    
    webview.start()
