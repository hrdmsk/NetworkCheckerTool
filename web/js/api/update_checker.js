// web/js/api_calls/update_checker.js

/**
 * Pythonから呼び出され、アップデート通知ポップアップを表示する
 * @param {string} newVersion - 見つかった新しいバージョン番号
 */
function show_update_notification(newVersion) {
    const modalOverlay = document.getElementById('update-modal-overlay');
    const modalTitle = document.getElementById('update-modal-title');
    const closeBtn = document.getElementById('update-modal-close');

    if (modalOverlay) {
        modalTitle.textContent = `アップデートのお知らせ (v${newVersion})`;
        modalOverlay.classList.add('show'); // CSSの transition を使って表示

        // 閉じるボタンがクリックされたら非表示にする
        closeBtn.onclick = () => {
            modalOverlay.classList.remove('show');
        };
        
        // オーバーレイ部分がクリックされても非表示にする
        modalOverlay.onclick = (event) => {
            if (event.target === modalOverlay) {
                modalOverlay.classList.remove('show');
            }
        };
    }
}
