async function startPing() {
    const host = document.getElementById('ping-host').value;
    const resultsDiv = document.getElementById('ping-results');
    if (!host) {
        resultsDiv.textContent = 'ホストを入力してください。';
        return;
    }
    resultsDiv.textContent = `実行中...`;
    showLoader('Pingを実行中...');
    try {
        resultsDiv.textContent = await window.pywebview.api.ping_py(host);
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
    } finally {
        hideLoader();
    }
}

async function startTraceroute() {
    const host = document.getElementById('traceroute-host').value;
    const resultsDiv = document.getElementById('traceroute-results');
    if (!host) {
        resultsDiv.textContent = 'ホストを入力してください。';
        return;
    }
    resultsDiv.textContent = `実行中... (時間がかかる場合があります)`;
    showLoader('経路を追跡中...');
    try {
        resultsDiv.textContent = await window.pywebview.api.traceroute_py(host);
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
    } finally {
        hideLoader();
    }
}