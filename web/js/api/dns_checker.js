// web/js/api_calls/nslookup.js
async function startLookup() {
    const domain = document.getElementById('domain').value;
    const resultsDiv = document.getElementById('nslookup-results');
    const dnsSelect = document.getElementById('dns-server-select');
    let server = dnsSelect.value;
    if (server === 'custom') { server = document.getElementById('custom-dns-server').value; }

    if (!domain) {
        resultsDiv.innerHTML = '<div class="error-message">ドメイン名を入力してください。</div>';
        return;
    }
    
    showLoader('DNSレコードを検索中...');
    try {
        const results = await window.pywebview.api.nslookup_py(domain, server);
        resultsDiv.innerHTML = '';
        if (results.error) {
            resultsDiv.innerHTML = `<div class="error-message">${results.error}</div>`;
            return;
        }
        results.forEach(item => {
            const card = document.createElement('div');
            card.className = 'result-card';
            const header = document.createElement('div');
            header.className = 'result-header';
            header.textContent = `${item.type} レコード`;
            const body = document.createElement('div');
            body.className = 'result-body';
            if (item.records && item.records.length > 0) {
                item.records.forEach(record => {
                    const p = document.createElement('p');
                    // textContentからinnerTextに変更し、改行を正しく表示
                    p.innerText = record; 
                    body.appendChild(p);
                });
            } else {
                const p = document.createElement('p');
                p.className = 'status-message';
                p.textContent = item.status || '情報がありません。';
                body.appendChild(p);
            }
            card.appendChild(header);
            card.appendChild(body);
            resultsDiv.appendChild(card);
        });
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error-message">アプリケーションで予期せぬエラーが発生しました。<br>${error}</div>`;
    } finally {
        hideLoader();
    }
}
