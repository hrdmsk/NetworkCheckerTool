// web/js/api_calls.js
// PythonのAPI呼び出しと、結果の表示を担当

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
                    p.textContent = record;
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

function formatWhoisForDisplay(text) {
    const escapeHtml = (unsafe) => unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return text.split('\n').map(line => {
        const escapedLine = escapeHtml(line);
        if (escapedLine.match(/Name Server|ネームサーバ/i)) { return `<span class="highlight-yellow">${escapedLine}</span>`; }
        if (escapedLine.match(/Date|日/i)) { return `<span class="highlight-green">${escapedLine}</span>`; }
        return escapedLine;
    }).join('\n');
}

async function startEmailAuthCheck() {
    const domain = document.getElementById('emailauth-domain').value;
    const selector = document.getElementById('dkim-selector').value;
    const resultsDiv = document.getElementById('emailauth-results');
    const selectorContainer = document.getElementById('checked-selectors-container');
    
    if (!domain) {
        resultsDiv.innerHTML = '<div class="error-message">ドメイン名を入力してください。</div>';
        return;
    }
    resultsDiv.innerHTML = '';
    selectorContainer.style.display = 'none';
    document.getElementById('dkim-progress-container').style.display = 'block';
    window.pywebview.api.check_email_auth_py(domain, selector);
}

function update_dkim_progress(done, total) {
    const progressBar = document.getElementById('dkim-progress-bar');
    const progressText = document.getElementById('dkim-progress-text');
    const percentage = total > 0 ? Math.round((done / total) * 100) : 0;
    progressBar.style.width = `${percentage}%`;
    progressText.textContent = `確認中... (${done} / ${total})`;
}

function finish_auth_check(response) {
    document.getElementById('dkim-progress-container').style.display = 'none';
    const resultsDiv = document.getElementById('emailauth-results');
    const selectorContainer = document.getElementById('checked-selectors-container');
    const selectorListDiv = document.getElementById('checked-selectors-list');

    if (response.error) {
        resultsDiv.innerHTML = `<div class="error-message">${response.error}</div>`;
        return;
    }
    const results = response.results;
    const checked_selectors = response.checked_selectors;
    results.forEach(item => {
        const card = document.createElement('div');
        card.className = 'result-card';
        const header = document.createElement('div');
        header.className = 'result-header';
        let headerText = `${item.type} レコード`;
        if (item.type === 'DKIM' && item.query) { headerText += ` (${item.query})`; }
        header.textContent = headerText;
        const body = document.createElement('div');
        body.className = 'result-body';
        if (item.records && item.records.length > 0) {
            item.records.forEach(record => {
                const p = document.createElement('p');
                p.textContent = record;
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
    if (checked_selectors && checked_selectors.length > 0) {
        selectorContainer.style.display = 'block';
        selectorListDiv.textContent = checked_selectors.join(', ');
    }
}
