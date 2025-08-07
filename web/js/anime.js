// anime.js

// グローバルスコープでローダー要素を保持する変数を宣言
let loaderOverlay;
let loaderText;

// DOMの読み込みが完了した時点で、一度だけ要素を取得
document.addEventListener('DOMContentLoaded', () => {
    loaderOverlay = document.getElementById('loader-overlay');
    loaderText = loaderOverlay.querySelector('.loader-text');
});

/**
 * ローディングアニメーションを表示する関数
 * @param {string} [message='処理中...'] - ローダーに表示するテキスト
 */
function showLoader(message = '処理中...') {
    if (loaderOverlay && loaderText) {
        loaderText.textContent = message;
        loaderOverlay.style.display = 'flex';
    }
}

/**
 * ローディングアニメーションを非表示にする関数
 */
function hideLoader() {
    if (loaderOverlay) {
        loaderOverlay.style.display = 'none';
    }
}
