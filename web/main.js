// --- ページの読み込み完了時の処理 ---
document.addEventListener('DOMContentLoaded', async () => {

    // --- タブとドロップダウンの制御ロジック ---
    const tabClickables = document.querySelectorAll('[data-tab]');
    const contentPanes = document.querySelectorAll('.tab-content');
    const allTabButtons = document.querySelectorAll('.tab-button');
    const dropdownBtn = document.getElementById('dropdown-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');

    tabClickables.forEach(clickable => {
        clickable.addEventListener('click', (event) => {
            event.preventDefault();
            const tabName = clickable.dataset.tab;

            contentPanes.forEach(pane => pane.classList.remove('active'));
            allTabButtons.forEach(btn => btn.classList.remove('active'));

            const activePane = document.getElementById(`${tabName}-tab`);
            if (activePane) {
                activePane.classList.add('active');
            }

            if (clickable.closest('.dropdown-content')) {
                if(dropdownBtn) dropdownBtn.classList.add('active');
            } else if(clickable.classList.contains('tab-button')) {
                clickable.classList.add('active');
            }

            if (dropdownMenu) dropdownMenu.classList.remove('show');
        });
    });

    if (dropdownBtn) {
        dropdownBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            if (dropdownMenu) dropdownMenu.classList.toggle('show');
        });
    }

    window.addEventListener('click', (event) => {
        if (dropdownBtn && !dropdownBtn.contains(event.target)) {
            if (dropdownMenu && dropdownMenu.classList.contains('show')) {
                dropdownMenu.classList.remove('show');
            }
        }
    });

    // --- DNSサーバーリストの読み込み ---
    const dnsSelect = document.getElementById('dns-server-select');
    const customDnsInput = document.getElementById('custom-dns-server');

    try {
        const response = await fetch('dns/dns_servers.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        const addOptionsToSelect = (servers, groupName) => {
            if (servers && servers.length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = groupName;
                servers.forEach(server => {
                    const option = document.createElement('option');
                    option.value = server.ip;
                    option.textContent = `${server.name} (${server.ip})`;
                    optgroup.appendChild(option);
                });
                dnsSelect.insertBefore(optgroup, dnsSelect.querySelector('option[value="custom"]'));
            }
        };

        addOptionsToSelect(data.public, 'Public DNS');
        addOptionsToSelect(data.authoritative, 'Authoritative NS');

    } catch (error) {
        console.error("DNSサーバーリストの読み込みに失敗しました:", error);
    }

    if(dnsSelect && customDnsInput) {
        dnsSelect.addEventListener('change', () => {
            customDnsInput.style.display = (dnsSelect.value === 'custom') ? 'block' : 'none';
        });
    }
    
    // --- ポート番号のドロップダウン制御 ---
    const portSelect = document.getElementById('portcheck-port-select');
    const customPortInput = document.getElementById('portcheck-port-custom');
    if (portSelect && customPortInput) {
        portSelect.addEventListener('change', () => {
            customPortInput.style.display = (portSelect.value === 'custom') ? 'block' : 'none';
        });
    }
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
    const resultsDiv = document.getElementById('portcheck-results');
    
    const portSelect = document.getElementById('portcheck-port-select');
    let port = portSelect.value;
    if (port === 'custom') {
        port = document.getElementById('portcheck-port-custom').value;
    }

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
        resultsDiv.innerHTML = formatWhoisForDisplay(resultText);
    } catch (error) {
        resultsDiv.textContent = 'アプリケーションでエラーが発生しました。\n' + error;
        console.error(error);
    } finally {
        hideLoader();
    }
}

/**
 * ★追加: Whoisの結果を色分けするヘルパー関数
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
        if (escapedLine.match(/Creation Date|Created|登録年月日|作成日/i)) {
            return `<span class="highlight-green">${escapedLine}</span>`;
        }
        if (escapedLine.match(/Updated Date|Last Update|最終更新日/i)) {
            return `<span class="highlight-green">${escapedLine}</span>`;
        }
        return escapedLine;
    });
    return formattedLines.join('\n');
}

/**
 * メール認証レコードを検索する非同期関数
 */
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

    // ★修正: 日付セレクタの引数を削除
    eel.check_email_auth_py(domain, selector)();
}

eel.expose(update_dkim_progress, 'update_dkim_progress');
function update_dkim_progress(done, total) {
    const progressBar = document.getElementById('dkim-progress-bar');
    const progressText = document.getElementById('dkim-progress-text');
    const percentage = total > 0 ? Math.round((done / total) * 100) : 0;
    
    progressBar.style.width = `${percentage}%`;
    progressText.textContent = `確認中... (${done} / ${total})`;
}

eel.expose(finish_auth_check, 'finish_auth_check');
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
