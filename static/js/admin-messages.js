/* Модальный просмотр сообщений обратной связи в списке и на сводке админки. */
document.addEventListener('DOMContentLoaded', () => {
    const OPENERS = '.message-open, .message-link';
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');

    let dialog = null;
    let fields = null;
    let opener = null;

    function createDialog() {
        const element = document.createElement('dialog');
        element.className = 'message-dialog';
        element.setAttribute('aria-labelledby', 'messageDialogTitle');
        element.innerHTML = `
            <div class="message-dialog-inner">
                <div class="message-dialog-header">
                    <h2 id="messageDialogTitle">Сообщение</h2>
                    <button type="button" class="message-dialog-close" data-close aria-label="Закрыть окно">
                        <span class="material-symbols-outlined" aria-hidden="true">close</span>
                    </button>
                </div>
                <dl class="message-dialog-meta">
                    <div><dt>От</dt><dd class="js-email"></dd></div>
                    <div><dt>Получено</dt><dd class="js-received"></dd></div>
                </dl>
                <p class="message-dialog-text js-text"></p>
                <div class="message-dialog-actions">
                    <a class="message-dialog-button primary js-reply" href="#">
                        <span class="material-symbols-outlined" aria-hidden="true">reply</span>Ответить
                    </a>
                    <a class="message-dialog-button js-full" href="#">Открыть полностью</a>
                    <button type="button" class="message-dialog-button" data-close>Закрыть</button>
                </div>
            </div>`;
        return element;
    }

    function showLoading() {
        fields.email.textContent = '…';
        fields.received.textContent = '…';
        fields.text.textContent = 'Загружаем сообщение…';
        fields.actions.hidden = true;
    }

    function showMessage(data) {
        fields.email.textContent = data.email;
        fields.received.textContent = data.received;
        fields.text.textContent = data.message;
        fields.reply.href = data.reply_url;
        fields.full.href = data.change_url;
        fields.actions.hidden = false;
    }

    function showError() {
        fields.text.textContent = 'Не удалось загрузить сообщение. Попробуйте обновить страницу.';
        fields.actions.hidden = true;
    }

    function markRowAsRead(trigger) {
        const row = trigger.closest('tr');
        const status = row && row.querySelector('.message-status');
        if (status) {
            status.classList.remove('is-unread');
            status.textContent = 'Прочитано';
        }
    }

    function prepareDialog() {
        if (dialog) return;
        dialog = createDialog();
        document.body.append(dialog);
        fields = {
            email: dialog.querySelector('.js-email'),
            received: dialog.querySelector('.js-received'),
            text: dialog.querySelector('.js-text'),
            reply: dialog.querySelector('.js-reply'),
            full: dialog.querySelector('.js-full'),
            actions: dialog.querySelector('.message-dialog-actions'),
        };

        dialog.addEventListener('click', (event) => {
            if (event.target === dialog || event.target.closest('[data-close]')) {
                dialog.close();
            }
        });

        dialog.addEventListener('close', () => {
            if (opener && opener.isConnected) opener.focus();
        });
    }

    async function openMessage(trigger) {
        prepareDialog();
        opener = trigger;
        showLoading();
        dialog.showModal();
        try {
            const response = await fetch(trigger.dataset.url, {
                method: 'POST',
                headers: { 'X-CSRFToken': tokenInput ? tokenInput.value : '' },
                credentials: 'same-origin',
            });
            if (!response.ok) throw new Error(`Сервер ответил ${response.status}`);
            const data = await response.json();
            showMessage(data);
            markRowAsRead(trigger);
            if (window.updateUnreadCount) window.updateUnreadCount(data.unread);
        } catch (error) {
            showError();
        }
    }

    // Делегируем клики на document, чтобы обработчик работал и после автообновления таблицы сводки.
    document.addEventListener('click', (event) => {
        const trigger = event.target.closest(OPENERS);
        if (trigger) {
            event.preventDefault();
            openMessage(trigger);
            return;
        }

        if (event.target.closest('input, a, button, label, select')) return;
        const row = event.target.closest('tr');
        const rowTrigger = row && row.querySelector(OPENERS);
        if (rowTrigger) openMessage(rowTrigger);
    });
});
