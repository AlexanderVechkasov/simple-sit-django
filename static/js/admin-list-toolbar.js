/* Панель массовых действий над списком записей в админке и очистка поля поиска. */
document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('changelist-search');
    if (searchForm) {
        const searchInput = searchForm.querySelector('#searchbar');
        const clearButton = searchForm.querySelector('[data-admin-search-clear]');
        if (searchInput && clearButton) {
            const hadQuery = searchInput.value.trim().length > 0;
            const syncClear = () => {
                clearButton.hidden = searchInput.value.length === 0;
            };
            searchInput.addEventListener('input', syncClear);
            clearButton.addEventListener('click', () => {
                searchInput.value = '';
                syncClear();
                if (hadQuery) {
                    searchForm.requestSubmit();
                } else {
                    searchInput.focus();
                }
            });
            syncClear();
        }
    }

    const toolbar = document.querySelector('[data-list-toolbar]');
    const form = document.getElementById('changelist-form');
    if (!toolbar || !form) return;

    const buttons = toolbar.querySelectorAll('[data-tool]');
    const statusText = toolbar.querySelector('.list-toolbar-status');
    const tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');

    toolbar.hidden = false;
    document.body.classList.add('list-toolbar-ready');

    function checkedBoxes() {
        return [...form.querySelectorAll('input.action-select:checked')];
    }

    function updateToolbar(message) {
        const count = checkedBoxes().length;
        buttons.forEach((button) => {
            button.disabled = button.dataset.needs === 'one' ? count !== 1 : count === 0;
        });
        if (message) {
            statusText.textContent = message;
        } else {
            statusText.textContent = count ? `Выбрано: ${count}` : 'Отметьте записи галочками';
        }
    }

    // Ждём следующий тик, чтобы обработчик action-toggle из Django успел обновить чекбоксы.
    form.addEventListener('change', () => setTimeout(() => updateToolbar()));

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

            boxes.forEach((box) => {
                const status = box.closest('tr').querySelector('.message-status');
                if (!status) return;
                status.classList.toggle('is-unread', action === 'unread');
                status.textContent = action === 'read' ? 'Прочитано' : 'Новое';
            });
            if (window.updateUnreadCount) window.updateUnreadCount(data.unread);

            clearSelection();
            const done = action === 'read' ? 'прочитанные' : 'непрочитанные';
            // Перезаписываем статус после асинхронного пересчёта из change-обработчика.
            setTimeout(() => updateToolbar(`Отмечено как ${done}: ${data.changed}`));
        } catch (error) {
            updateToolbar('Не получилось. Попробуйте обновить страницу.');
        }
    }

    function editSelected() {
        const [box] = checkedBoxes();
        const link = box && box.closest('tr').querySelector('a[href*="/change/"]');
        if (link) window.location.href = link.href;
    }

    function deleteSelected(button) {
        const select = form.querySelector('select[name="action"]');
        const runButton = form.querySelector('button[name="index"]');
        if (!select || !runButton || !window.askDelete) return;

        window.askDelete({
            title: 'Удалить выбранное?',
            text: `Будут удалены выбранные записи: ${checkedBoxes().length}. `
                + 'Это действие нельзя отменить.',
            trigger: button,
            confirm: () => {
                select.value = 'delete_selected';
                // post=yes подтверждает массовое удаление Django без промежуточной страницы.
                const confirmed = document.createElement('input');
                confirmed.type = 'hidden';
                confirmed.name = 'post';
                confirmed.value = 'yes';
                form.append(confirmed);
                form.requestSubmit(runButton);
            },
        });
    }

    toolbar.addEventListener('click', (event) => {
        const button = event.target.closest('[data-tool]');
        if (!button || button.disabled) return;
        const tool = button.dataset.tool;
        if (tool === 'read' || tool === 'unread') markSelected(tool);
        if (tool === 'edit') editSelected();
        if (tool === 'delete') deleteSelected(button);
    });

    updateToolbar();
});
