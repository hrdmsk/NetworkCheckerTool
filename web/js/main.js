// web/js/main.js
// UIの操作（タブ、ドロップダウン、設定など）のみを担当

document.addEventListener('DOMContentLoaded', async () => {
    // --- タブとドロップダウンの制御ロジック ---
    const tabLinks = document.querySelectorAll('.tab-nav .tab-link, .dropdown-content a');
    const contentPanes = document.querySelectorAll('.tab-content');
    const dropdownBtn = document.getElementById('dropdown-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');
    tabLinks.forEach(link => {
        // ドロップダウンの親ボタン自体はタブ切り替えを行わないので除外
        if (link.id === 'dropdown-btn') return;

        link.addEventListener('click', (event) => {
            event.preventDefault();
            const tabName = link.dataset.tab;

            // 全てのコンテンツを非表示にし、全てのリンクのアクティブ状態を解除
            contentPanes.forEach(pane => pane.classList.remove('active'));
            document.querySelectorAll('.tab-nav .tab-link').forEach(l => l.classList.remove('active'));

            // 対応するコンテンツを表示
            const activePane = document.getElementById(`${tabName}-tab`);
            if (activePane) { activePane.classList.add('active'); }

            // クリックされたリンクをアクティブにする
            if (link.closest('.dropdown-content')) {
                if(dropdownBtn) dropdownBtn.classList.add('active');
            } else {
                link.classList.add('active');
            }

            if (dropdownMenu) dropdownMenu.classList.remove('show');
        });
    });

    if (dropdownBtn) {
        dropdownBtn.addEventListener('click', (event) => {
            event.preventDefault();
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

    // --- 最前面表示の切り替えロジック ---
    const onTopToggle = document.getElementById('on-top-toggle');
    if (onTopToggle) {
        onTopToggle.addEventListener('change', () => {
            window.pywebview.api.toggle_on_top(onTopToggle.checked);
        });
    }

    // --- DNSサーバーリストの読み込み ---
    const dnsSelect = document.getElementById('dns-server-select');
    const customDnsInput = document.getElementById('custom-dns-server');
    const domainInput = document.getElementById('domain');
    const nslookupBtn = document.getElementById('nslookup-btn');

    try {
        const response = await fetch('dns/dns_servers.json');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        dnsSelect.innerHTML = '';
        dnsSelect.add(new Option('システムのデフォルト', ''));
        dnsSelect.add(new Option('カスタム...', 'custom'));
        
        const addOptionsToSelect = (servers, groupName) => {
            if (servers && servers.length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = groupName;
                servers.forEach(server => {
                    const option = new Option(`${server.name} (${server.ip})`, server.ip);
                    if (server.name.toLowerCase() === 'google') {
                        option.selected = true;
                    }
                    optgroup.appendChild(option);
                });
                dnsSelect.appendChild(optgroup);
            }
        };
        addOptionsToSelect(data.public, 'Public DNS');
        addOptionsToSelect(data.authoritative, 'Authoritative NS');

    } catch (error) {
        console.error("DNSサーバーリストの読み込みに失敗しました:", error);
        dnsSelect.innerHTML = '<option value="" disabled selected>サーバーリスト読込エラー</option>';
        dnsSelect.disabled = true;
        domainInput.disabled = true;
        nslookupBtn.disabled = true;
        document.getElementById('nslookup-results').innerHTML = 
            '<div class="error-message">DNSサーバーリスト(dns_servers.json)の読み込みに失敗したため、NSLOOKUP機能は無効化されました。</div>';
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
    const nslookupResults = document.getElementById('nslookup-results');
    if (nslookupResults) {
        nslookupResults.addEventListener('click', (event) => {
            // クリックされたのがWhoisボタンか確認
            if (event.target.classList.contains('ip-lookup-btn')) {
                const ip = event.target.dataset.ip;
                if (ip) {
                    console.log(`IP to lookup: ${ip}`);
                    // 1. Whoisタブの入力欄にIPを自動入力
                    document.getElementById('whois-target').value = ip;
                    // 2. Whoisタブに切り替え
                    document.querySelector('.tab-nav a[data-tab="whois"]').click();
                    // 3. Whois検索を自動実行
                    startWhois();
                }
            }
        });
    }
});

