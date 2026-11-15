/*
 * Админка → «Сообщения»: панель кнопок над списком, как в почте.
 *
 * «Прочитано» и «Не прочитано» меняют статус отмеченных сообщений
 * без перезагрузки страницы (наш адрес …/bulk/).
 * «Удалить» спрашивает подтверждение в окне и запускает обычное
 * действие Django «Удалить выбранные» — после него страница обновится.
 */
document.addEventListener('DOMContentLoaded', () => {
    const toolbar = document.querySelector('[data-message-toolbar]');
    const form = document.getElementById('changelist-form');
    if (!toolbar || !form) return;

    const buttons = toolbar.querySelectorAll('[data-bulk]');
    const statusText = toolbar.querySelector('.message-toolbar-status');
    const tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');

    // Показываем нашу панель и прячем стандартную панель действий Unfold.
    toolbar.hidden = false;
    document.body.classList.add('message-toolbar-ready');

    function checkedBoxes() {
        return [...form.querySelectorAll('input.action-select:checked')];
    }

    // Кнопки активны, только когда что-то отмечено.
    function updateToolbar(message) {
        const count = checkedBoxes().length;
        buttons.forEach((button) => {
            button.disabled = count === 0;
        });
        if (message) {
            statusText.textContent = message;
        } else {
            statusText.textContent = count ? `Выбрано: ${count}` : 'Отметьте сообщения галочками';
        }
    }

    // Галочки (и «выбрать все») меняет ещё и скрипт Django, поэтому
    // пересчитываем после того, как он закончит (setTimeout 0).
    form.addEventListener('change', () => setTimeout(() => updateToolbar()));

    // Снять все галочки — так же, как это сделал бы пользователь.
    function clearSelection() {
        const toggle = document.getElementById('action-toggle');
        if (toggle && toggle.checked) toggle.click();
        checkedBoxes().forEach((box) => box.click());
    }

    async function markSelected(action) {
        const boxes = checkedBoxes();
        const body = new FormData();
        body.append('action', action);
        boxes.forEach((box) => body.append('ids', box.value));

        try {
            const response = await fetch(toolbar.dataset.bulkUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': tokenInput ? tokenInput.value : '' },
                body,
                credentials: 'same-origin',
            });
            if (!response.ok) throw new Error(`Сервер ответил ${response.status}`);
            const data = await response.json();

            // Меняем статус в строках, которые были отмечены.
            boxes.forEach((box) => {
                const status = box.closest('tr').querySelector('.message-status');
                if (!status) return;
                status.classList.toggle('is-unread', action === 'unread');
                status.textContent = action === 'read' ? 'Прочитано' : 'Новое';
            });
            if (window.updateUnreadCount) window.updateUnreadCount(data.unread);

            clearSelection();
            const done = action === 'read' ? 'прочитанные' : 'непрочитанные';
            // После пересчёта галочек (он тоже идёт через setTimeout) — наш итог.
            setTimeout(() => updateToolbar(`Отмечено как ${done}: ${data.changed}`));
        } catch (error) {
            updateToolbar('Не получилось. Попробуйте обновить страницу.');
        }
    }

    // ---- Удаление: подтверждение в окне ----

    const confirmDialog = document.createElement('dialog');
    confirmDialog.className = 'message-dialog';
    confirmDialog.setAttribute('role', 'alertdialog');
    confirmDialog.setAttribute('aria-labelledby', 'deleteDialogTitle');
    confirmDialog.setAttribute('aria-describedby', 'deleteDialogText');
    confirmDialog.innerHTML = `
        <div class="message-dialog-inner">
            <div class="message-dialog-header">
                <h2 id="deleteDialogTitle">Удалить сообщения?</h2>
            </div>
            <p class="message-dialog-text" id="deleteDialogText"></p>
            <div class="message-dialog-actions">
                <button type="button" class="message-dialog-button danger" data-confirm>
                    <span class="material-symbols-outlined" aria-hidden="true">delete</span>Удалить
                </button>
                <button type="button" class="message-dialog-button" data-close>Отмена</button>
            </div>
        </div>`;
    document.body.append(confirmDialog);

    const deleteButton = toolbar.querySelector('[data-bulk="delete"]');

    confirmDialog.addEventListener('click', (event) => {
        if (event.target === confirmDialog || event.target.closest('[data-close]')) {
            confirmDialog.close();
        }
        if (event.target.closest('[data-confirm]')) {
            deleteSelected();
        }
    });
    confirmDialog.addEventListener('close', () => {
        if (deleteButton) deleteButton.focus();
    });

    function askDelete() {
        const count = checkedBoxes().length;
        confirmDialog.querySelector('#deleteDialogText').textContent =
            `Будет удалено сообщений: ${count}. Это действие нельзя отменить.`;
        confirmDialog.showModal();
        // Фокус на «Отмена» — случайный Enter ничего не удалит.
        confirmDialog.querySelector('[data-close]').focus();
    }

    // Запускаем стандартное действие Django «Удалить выбранные».
    // post=yes — это ответ «Да, я уверен» вместо отдельной страницы подтверждения.
    function deleteSelected() {
        const select = form.querySelector('select[name="action"]');
        const runButton = form.querySelector('button[name="index"]');
        if (!select || !runButton) return;

        select.value = 'delete_selected';
        const confirmed = document.createElement('input');
        confirmed.type = 'hidden';
        confirmed.name = 'post';
        confirmed.value = 'yes';
        form.append(confirmed);
        form.requestSubmit(runButton);
    }

    toolbar.addEventListener('click', (event) => {
        const button = event.target.closest('[data-bulk]');
        if (!button || button.disabled) return;
        if (button.dataset.bulk === 'delete') {
            askDelete();
        } else {
            markSelected(button.dataset.bulk);
        }
    });

    updateToolbar();
});
