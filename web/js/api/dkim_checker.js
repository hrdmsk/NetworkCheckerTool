// web/js/api_calls/dkim_checker.js

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

        header.innerHTML = `
            <span class="result-header-title">${headerText}</span>
            <button class="clipboard-btn-card" title="この結果をコピー">📋</button>
        `;

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
