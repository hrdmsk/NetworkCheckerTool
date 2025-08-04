/**
 * ボタンがクリックされたときに実行される非同期関数
 */
async function startLookup() {
    // HTMLから入力要素を取得
    const domainInput = document.getElementById('domain');
    const serverInput = document.getElementById('server');
    const resultsDiv = document.getElementById('results');

    // 入力値を取得
    const domain = domainInput.value;
    const server = serverInput.value;

    // ドメインが入力されていなければ処理を中断
    if (!domain) {
        resultsDiv.textContent = 'ドメイン名を入力してください。';
        return;
    }

    // 検索中であることをユーザーにフィードバック
    resultsDiv.textContent = '検索中...';

    try {
        // Pythonの nslookup_py 関数を呼び出し、結果が返ってくるのを待つ (await)
        // eel.python_function_name(args) の形式で呼び出す
        const resultText = await eel.nslookup_py(domain, server)();
        
        // Pythonから受け取った結果をHTMLの<pre>タグに表示
        resultsDiv.textContent = resultText;
    } catch (error) {
        // Python側の処理で予期せぬエラーが発生した場合
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    }
}
