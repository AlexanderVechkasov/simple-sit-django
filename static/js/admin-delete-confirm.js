/*
 * Админка: подтверждение удаления во всплывающем окне вместо отдельной страницы.
 *
 * Работает для всех разделов админки:
 *  - кнопка «Удалить …» внизу формы записи (например, события);
 *  - действие «Удалить выбранные …» в списке записей.
 *
 * Окно спрашивает «Удалить?». После «Удалить» запускается обычное удаление
 * Django: права проверяет сервер, а если удалить нельзя (нет прав или запись
 * защищена), Django сам покажет свою страницу с объяснением.
 *
 * Подключается на всех страницах админки через UNFOLD["SCRIPTS"].
 */
document.addEventListener('DOMContentLoaded', () => {
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');

    let dialog = null;
    let onConfirm = null;  // что сделать, если нажали «Удалить»
    let returnFocus = null; // куда вернуть фокус, если передумали

    // Окно создаём один раз, при первом удалении. Стили — те же, что у окна
    // сообщений (.message-dialog в static/css/admin.css).
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
                returnFocus = null; // страница сейчас уйдёт — фокус возвращать некуда
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
    // Доступна и другим скриптам: её вызывает панель кнопок над списком
    // (admin-list-toolbar.js), чтобы окно было одно на всю админку.
    window.askDelete = askDelete;
    function askDelete({ title, text, trigger, confirm }) {
        prepareDialog();
        dialog.querySelector('#confirmDeleteTitle').textContent = title;
        dialog.querySelector('#confirmDeleteText').textContent = text;
        onConfirm = confirm;
        returnFocus = trigger;
        dialog.showModal();
        // Фокус на «Отмена» — случайный Enter ничего не удалит.
        dialog.querySelector('[data-close]').focus();
    }

    // ---- 1. Кнопка «Удалить …» внизу формы записи ----
    // Это ссылка на адрес …/<номер>/delete/. Вместо перехода на страницу
    // подтверждения спрашиваем в окне и сразу отправляем POST на тот же адрес.
    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[href]');
        if (!link || !new URL(link.href).pathname.endsWith('/delete/')) return;

        event.preventDefault();
        const label = link.textContent.trim().replace(/\s+/g, ' '); // «Удалить событие»
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

    // ---- 2. Действие «Удалить выбранные …» в списке записей ----
    const changelistForm = document.getElementById('changelist-form');
    if (!changelistForm) return;

    changelistForm.addEventListener('submit', (event) => {
        const select = changelistForm.querySelector('select[name="action"]');
        if (!select || select.value !== 'delete_selected') return;
        /* Панель кнопок над списком записей (как в почте) */
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
                // post=yes — ответ «Да, я уверен» вместо страницы подтверждения Django.
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
