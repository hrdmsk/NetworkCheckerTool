/**
 * 指定されたタブを表示し、他を非表示にする関数
 * @param {string} tabName - 表示するタブの名前 ('nslookup' or 'portcheck')
 */
function showTab(tabName) {
    // すべてのタブコンテンツを非表示にする
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.remove('active'));

    // すべてのタブボタンのハイライトを解除
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => button.classList.remove('active'));

    // 指定されたタブコンテンツとボタンをアクティブにする
    document.getElementById(tabName + '-tab').classList.add('active');
    document.querySelector(`button[onclick="showTab('${tabName}')"]`).classList.add('active');
}

/**
 * NSLOOKUPを実行する非同期関数
 */
async function startLookup() {
    const domain = document.getElementById('domain').value;
    const server = document.getElementById('server').value;
    const resultsDiv = document.getElementById('nslookup-results');

    if (!domain) {
        resultsDiv.textContent = 'ドメイン名を入力してください。';
        return;
    }
    resultsDiv.textContent = '検索中...';

    try {
        const resultText = await eel.nslookup_py(domain, server)();
        resultsDiv.textContent = resultText;
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    }
}

/**
 * ポート接続テストを実行する非同期関数
 */
async function startPortCheck() {
    const host = document.getElementById('portcheck-host').value;
    const port = document.getElementById('portcheck-port').value;
    const resultsDiv = document.getElementById('portcheck-results');

    if (!host || !port) {
        resultsDiv.textContent = 'ホストとポート番号の両方を入力してください。';
        return;
    }
    resultsDiv.textContent = '接続を試みています...';

    try {
        // Pythonの test_port_connection_py 関数を呼び出す
        const resultText = await eel.test_port_connection_py(host, port)();
        resultsDiv.textContent = resultText;
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    }
}
