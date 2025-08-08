/** DNS Checker JavaScript */

async function startPortCheck() {
    const host = document.getElementById('portcheck-host').value;
    const resultsDiv = document.getElementById('portcheck-results');
    const portSelect = document.getElementById('portcheck-port-select');
    let port = portSelect.value;
    if (port === 'custom') { port = document.getElementById('portcheck-port-custom').value; }

    if (!host || !port) {
        resultsDiv.textContent = 'ホストとポート番号の両方を入力してください。';
        return;
    }
    showLoader('ポートに接続中...');
    try {
        resultsDiv.textContent = await window.pywebview.api.test_port_connection_py(host, port);
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
    } finally {
        hideLoader();
    }
}