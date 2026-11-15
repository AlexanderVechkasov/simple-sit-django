/*
 * Админка: просмотр сообщения во всплывающем окне.
 *
 * Работает в списке «Сообщения» и в таблице «Последние сообщения» на «Сводке».
 * Окно открывается кнопкой «Прочитать», ссылкой на сообщение
 * или кликом по строке.
 * Данные приходят с нашего адреса …/<номер>/read/, и сообщение там же
 * отмечается прочитанным. Статус в строке и число в меню меняются сразу,
 * без перезагрузки страницы.
 *
 * Клики ловим на всём документе (делегирование событий), поэтому окно
 * открывается и для строк, которые появились позже — например, когда
 * таблица на «Сводке» обновилась сама.
 */
document.addEventListener('DOMContentLoaded', () => {
    // .message-open — кнопка «Прочитать» в списке, .message-link — ссылка на «Сводке»
    const OPENERS = '.message-open, .message-link';

    // CSRF-токен берём из формы, которая есть на каждой странице админки
    // (например, кнопка «Выйти»).
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');

    let dialog = null;  // окно создаём при первом открытии
    let fields = null;
    let opener = null;  // кнопка или ссылка, откуда открыли окно

    // Разметка окна. Здесь нет данных посетителя — их вставляем ниже
    // через textContent, поэтому чужой HTML выполниться не может.
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

    // Статус «Новое» → «Прочитано» прямо в строке списка.
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

        // Закрытие: кнопки с data-close или клик по затемнённому фону. Esc — сам браузер.
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog || event.target.closest('[data-close]')) {
                dialog.close();
            }
        });

        // После закрытия фокус возвращается туда, откуда окно открыли
        // (если этой строки уже нет — например, таблица обновилась, — ничего не делаем).
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
            // Число непрочитанных в меню и на «Сводке» (функция из admin-live.js)
            if (window.updateUnreadCount) window.updateUnreadCount(data.unread);
        } catch (error) {
            showError();
        }
    }

    document.addEventListener('click', (event) => {
        // Клик по кнопке «Прочитать» или ссылке на сообщение
        const trigger = event.target.closest(OPENERS);
        if (trigger) {
            event.preventDefault(); // ссылка не уходит на другую страницу
            openMessage(trigger);
            return;
        }

        // Клик по любому другому месту строки с сообщением —
        // кроме галочки выбора, ссылок и кнопок.
        if (event.target.closest('input, a, button, label, select')) return;
        const row = event.target.closest('tr');
        const rowTrigger = row && row.querySelector(OPENERS);
        if (rowTrigger) openMessage(rowTrigger);
    });
});
