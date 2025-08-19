// web/js/clipboard_handler.js

/**
 * クリップボードへのコピーを実行し、ボタンの表示を更新する
 * @param {HTMLElement} button - クリックされたボタン要素
 * @param {string} textToCopy - コピーするテキスト
 */
function copyToClipboard(button, textToCopy) {
    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalHTML = button.innerHTML;
        button.innerHTML = '✅';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('クリップボードへのコピーに失敗しました:', err);
        alert('コピーに失敗しました。');
    });
}

/**
 * 動的に生成されるカード内のコピーボタンのクリックを処理する (イベント委譲)
 * @param {Event} event - クリックイベント
 */
function handleCardCopyClick(event) {
    const button = event.target.closest('.clipboard-btn-card'); // 
    if (button) {
        const card = button.closest('.result-card');
        if (card) {
            const header = card.querySelector('.result-header-title').innerText;
            const body = card.querySelector('.result-body').innerText;
            const textToCopy = `--- ${header} ---\n${body}`;
            copyToClipboard(button, textToCopy);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // --- イベント委譲の設定 (カード形式の結果) ---
    const nslookupResults = document.getElementById('nslookup-results');
    const emailAuthResults = document.getElementById('emailauth-results');

    if (nslookupResults) {
        nslookupResults.addEventListener('click', handleCardCopyClick);
    }
    if (emailAuthResults) {
        emailAuthResults.addEventListener('click', handleCardCopyClick);
    }

    // --- 静的な結果表示エリアのコピーボタン ---
    const staticCopyButtons = document.querySelectorAll('.clipboard-btn'); // ★変更
    staticCopyButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetId = button.dataset.target;
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                copyToClipboard(button, targetElement.innerText);
            }
        });
    });
});
