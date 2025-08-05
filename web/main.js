/**
 * 指定されたタブを表示し、他を非表示にする関数
 */
function showTab(tabName) {
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.remove('active'));
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => button.classList.remove('active'));
    document.getElementById(tabName + '-tab').classList.add('active');
    document.querySelector(`button[onclick="showTab('${tabName}')"]`).classList.add('active');
}

// --- ローディングアニメーション制御 ---
let loaderOverlay;
let loaderText;

function showLoader(message = '処理中...') {
    if (loaderOverlay && loaderText) {
        loaderText.textContent = message;
        loaderOverlay.style.display = 'flex';
    }
}

function hideLoader() {
    if (loaderOverlay) {
        loaderOverlay.style.display = 'none';
    }
}

// ページの読み込みが完了したら、イベントリスナーを設定
document.addEventListener('DOMContentLoaded', async () => {
    loaderOverlay = document.getElementById('loader-overlay');
    loaderText = loaderOverlay.querySelector('.loader-text');

    const dnsSelect = document.getElementById('dns-server-select');
    const customDnsInput = document.getElementById('custom-dns-server');

    try {
        const response = await fetch('dns_servers.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const servers = await response.json();

        servers.forEach(server => {
            const option = document.createElement('option');
            option.value = server.ip;
            option.textContent = `${server.name} (${server.ip})`;
            if (server.name === 'Google') {
                option.selected = true;
            }
            dnsSelect.insertBefore(option, dnsSelect.querySelector('option[value="custom"]'));
        });
    } catch (error) {
        console.error("DNSサーバーリストの読み込みに失敗しました:", error);
        const errorOption = document.createElement('option');
        errorOption.textContent = 'リスト読込エラー';
        errorOption.disabled = true;
        dnsSelect.insertBefore(errorOption, dnsSelect.querySelector('option[value="custom"]'));
    }

    dnsSelect.addEventListener('change', () => {
        customDnsInput.style.display = (dnsSelect.value === 'custom') ? 'block' : 'none';
    });
});


/**
 * NSLOOKUPを実行する非同期関数
 */
async function startLookup() {
    const domain = document.getElementById('domain').value;
    const resultsDiv = document.getElementById('nslookup-results');
    
    const dnsSelect = document.getElementById('dns-server-select');
    let server = dnsSelect.value;
    if (server === 'custom') {
        server = document.getElementById('custom-dns-server').value;
    }

    if (!domain) {
        resultsDiv.innerHTML = '<div class="error-message">ドメイン名を入力してください。</div>';
        return;
    }
    
    showLoader('DNSレコードを検索中...');

    try {
        const results = await eel.nslookup_py(domain, server)();
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
                const status = document.createElement('p');
                status.className = 'status-message';
                status.textContent = item.status || '情報がありません。';
                body.appendChild(status);
            }
            card.appendChild(header);
            card.appendChild(body);
            resultsDiv.appendChild(card);
        });

    } catch (error) {
        resultsDiv.innerHTML = `<div class="error-message">アプリケーションで予期せぬエラーが発生しました。<br>${error}</div>`;
        console.error(error);
    } finally {
        hideLoader();
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
    
    showLoader('ポートに接続中...');

    try {
        const resultText = await eel.test_port_connection_py(host, port)();
        resultsDiv.textContent = resultText;
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    } finally {
        hideLoader();
    }
}

/**
 * Pingを実行する非同期関数
 */
async function startPing() {
    const host = document.getElementById('ping-host').value;
    const resultsDiv = document.getElementById('ping-results');

    if (!host) {
        resultsDiv.textContent = 'ホストを入力してください。';
        return;
    }
    
    const command = `ping -n 4 ${host}`;
    resultsDiv.textContent = `[実行中のコマンド: ${command}]\n\n実行中...`;
    showLoader('Pingを実行中...');
    
    try {
        const resultText = await eel.ping_py(host)();
        resultsDiv.textContent = `[実行したコマンド: ${command}]\n\n${resultText}`;
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    } finally {
        hideLoader();
    }
}

/**
 * Tracerouteを実行する非同期関数
 */
async function startTraceroute() {
    const host = document.getElementById('traceroute-host').value;
    const resultsDiv = document.getElementById('traceroute-results');

    if (!host) {
        resultsDiv.textContent = 'ホストを入力してください。';
        return;
    }
    
    const command = `tracert ${host}`;
    resultsDiv.textContent = `[実行中のコマンド: ${command}]\n\n実行中... (時間がかかる場合があります)`;
    showLoader('経路を追跡中...');

    try {
        const resultText = await eel.traceroute_py(host)();
        resultsDiv.textContent = `[実行したコマンド: ${command}]\n\n${resultText}`;
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    } finally {
        hideLoader();
    }
}

/**
 * Whois情報を取得する非同期関数
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
        const resultText = await eel.whois_py(target)();
        resultsDiv.textContent = resultText;
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    } finally {
        hideLoader();
    }
}

/**
 * メール認証レコードを検索する非同期関数
 */
async function startEmailAuthCheck() {
    const domain = document.getElementById('emailauth-domain').value;
    const selector = document.getElementById('dkim-selector').value;
    const resultsDiv = document.getElementById('emailauth-results');

    if (!domain) {
        resultsDiv.innerHTML = '<div class="error-message">ドメイン名を入力してください。</div>';
        return;
    }

    showLoader('認証レコードを検索中...');

    try {
        const results = await eel.check_email_auth_py(domain, selector)();
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
            let headerText = `${item.type} レコード`;
            if (item.type === 'DKIM' && item.query) {
                headerText += ` (${item.query})`;
            }
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
                const status = document.createElement('p');
                status.className = 'status-message';
                status.textContent = item.status || '情報がありません。';
                body.appendChild(status);
            }
            
            card.appendChild(header);
            card.appendChild(body);
            resultsDiv.appendChild(card);
        });

    } catch (error) {
        resultsDiv.innerHTML = `<div class="error-message">アプリケーションで予期せぬエラーが発生しました。<br>${error}</div>`;
        console.error(error);
    } finally {
        hideLoader();
    }
}
