import webview
import sys
import os
from api import Api, set_window_for_api

# 最新バージョンが記載されたテキストファイルのURLのみを定義
VERSION_URL = "https://raw.githubusercontent.com/hrdmsk/RentalServerChecker/main/version.txt" 

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
    
    set_window_for_api(window) 
    
    def on_loaded():
        api.check_for_updates(VERSION_URL)

    def on_closed():
        print('ウィンドウが閉じられました。アプリケーションを終了します。')

    window.events.loaded += on_loaded
    window.events.closed += on_closed
    
    webview.start()
