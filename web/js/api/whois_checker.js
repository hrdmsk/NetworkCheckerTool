/**
 * Whois Checker JavaScript
 */
async function startWhois() {
    const target = document.getElementById('whois-target').value;
    const resultsDiv = document.getElementById('whois-results');
    if (!target) {
        resultsDiv.textContent = 'ドメイン名またはIPアドレスを入力してください。';
        return;
    }
    showLoader('Whois情報を取得中...');
    try {
        const resultText = await window.pywebview.api.whois_py(target);
        resultsDiv.innerHTML = formatWhoisForDisplay(resultText);
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
    } finally {
        hideLoader();
    }
}

/**
 * Whoisの結果を色分けするヘルパー関数
 */
function formatWhoisForDisplay(text) {
    const escapeHtml = (unsafe) => 
        unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    const lines = text.split('\n');
    const formattedLines = lines.map(line => {
        const escapedLine = escapeHtml(line);
        if (escapedLine.match(/Name Server|ネームサーバ/i)) {
            return `<span class="highlight-yellow">${escapedLine}</span>`;
        }
        // ハイライトするキーワードを限定
        if (escapedLine.match(/Creation Date|Updated Date|Expiration Date|Expiry Date|登録年月日|有効期限|最終更新/i)) {
            return `<span class="highlight-green">${escapedLine}</span>`;
        }
        return escapedLine;
    });
    return formattedLines.join('\n');
}