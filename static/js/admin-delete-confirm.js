/* Подтверждение удаления в админке через <dialog> вместо отдельной страницы Django. */
document.addEventListener('DOMContentLoaded', () => {
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');

    let dialog = null;
    let onConfirm = null;
    let returnFocus = null;

    function prepareDialog() {
        if (dialog) return;
        dialog = document.createElement('dialog');
        dialog.className = 'message-dialog';
        dialog.setAttribute('role', 'alertdialog');
        dialog.setAttribute('aria-labelledby', 'confirmDeleteTitle');
        dialog.setAttribute('aria-describedby', 'confirmDeleteText');
        dialog.innerHTML = `
            <div class="message-dialog-inner">
                <div class="message-dialog-header">
                    <h2 id="confirmDeleteTitle"></h2>
                </div>
                <p class="message-dialog-text" id="confirmDeleteText"></p>
                <div class="message-dialog-actions">
                    <button type="button" class="message-dialog-button danger" data-confirm>
                        <span class="material-symbols-outlined" aria-hidden="true">delete</span>Удалить
                    </button>
                    <button type="button" class="message-dialog-button" data-close>Отмена</button>
                </div>
            </div>`;
        document.body.append(dialog);

        dialog.addEventListener('click', (event) => {
            if (event.target.closest('[data-confirm]')) {
                const action = onConfirm;
                onConfirm = null;
                returnFocus = null;
                dialog.close();
                if (action) action();
            } else if (event.target === dialog || event.target.closest('[data-close]')) {
                dialog.close();
            }
        });

        dialog.addEventListener('close', () => {
            if (returnFocus) returnFocus.focus();
        });
    }

    // Используется также из admin-list-toolbar.js, чтобы диалог был единым на всю админку.
    window.askDelete = askDelete;
    function askDelete({ title, text, trigger, confirm }) {
        prepareDialog();
        dialog.querySelector('#confirmDeleteTitle').textContent = title;
        dialog.querySelector('#confirmDeleteText').textContent = text;
        onConfirm = confirm;
        returnFocus = trigger;
        dialog.showModal();
        // Фокус на «Отмена» защищает от случайного удаления по Enter.
        dialog.querySelector('[data-close]').focus();
    }

    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[href]');
        if (!link || !new URL(link.href).pathname.endsWith('/delete/')) return;

        event.preventDefault();
        const label = link.textContent.trim().replace(/\s+/g, ' ');
        askDelete({
            title: `${label}?`,
            text: 'Вместе с записью удалятся и связанные с ней данные '
                + '(например, картинки события). Это действие нельзя отменить.',
            trigger: link,
            confirm: () => {
                const form = document.createElement('form');
                form.method = 'post';
                form.action = link.href;
                form.innerHTML = '<input type="hidden" name="csrfmiddlewaretoken">'
                    + '<input type="hidden" name="post" value="yes">';
                form.querySelector('[name="csrfmiddlewaretoken"]').value = tokenInput ? tokenInput.value : '';
                document.body.append(form);
                form.submit();
            },
        });
    });

    const changelistForm = document.getElementById('changelist-form');
    if (!changelistForm) return;

    changelistForm.addEventListener('submit', (event) => {
        const select = changelistForm.querySelector('select[name="action"]');
        if (!select || select.value !== 'delete_selected') return;
        if (changelistForm.querySelector('input[name="post"]')) return;

        event.preventDefault();
        const runButton = event.submitter;
        const selectAcross = changelistForm.querySelector('input[name="select_across"]');
        const count = changelistForm.querySelectorAll('input.action-select:checked').length;
        const what = selectAcross && selectAcross.value === '1'
            ? 'все записи, подходящие под фильтр'
            : `выбранные записи: ${count}`;

        askDelete({
            title: 'Удалить выбранное?',
            text: `Будут удалены ${what}. Вместе с ними удалятся и связанные данные `
                + '(например, картинки событий). Это действие нельзя отменить.',
            trigger: runButton,
            confirm: () => {
                // post=yes подтверждает массовое удаление Django без промежуточной страницы.
                const confirmed = document.createElement('input');
                confirmed.type = 'hidden';
                confirmed.name = 'post';
                confirmed.value = 'yes';
                changelistForm.append(confirmed);
                changelistForm.requestSubmit(runButton);
            },
        });
    });
});
