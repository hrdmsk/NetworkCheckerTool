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

// ページの読み込みが完了したら、イベントリスナーを設定
document.addEventListener('DOMContentLoaded', () => {
    const dnsSelect = document.getElementById('dns-server-select');
    const customDnsInput = document.getElementById('custom-dns-server');

    // プルダウンメニューの値が変更されたときの処理
    dnsSelect.addEventListener('change', () => {
        // もし「カスタム」が選ばれたら、カスタム入力欄を表示
        if (dnsSelect.value === 'custom') {
            customDnsInput.style.display = 'block';
        } else {
            // それ以外の場合は非表示
            customDnsInput.style.display = 'none';
        }
    });
});


/**
 * NSLOOKUPを実行する非同期関数
 */
async function startLookup() {
    const domain = document.getElementById('domain').value;
    const resultsDiv = document.getElementById('nslookup-results');

    // DNSサーバーの選択値を取得
    const dnsSelect = document.getElementById('dns-server-select');
    let server = dnsSelect.value;
    // もし「カスタム」が選択されていたら、カスタム入力欄の値を使用
    if (server === 'custom') {
        server = document.getElementById('custom-dns-server').value;
    }

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
        const resultText = await eel.test_port_connection_py(host, port)();
        resultsDiv.textContent = resultText;
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    }
}
