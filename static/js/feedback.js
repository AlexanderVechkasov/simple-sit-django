/* Модальная отправка формы обратной связи через fetch с фолбэком на /feedback/. */
document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.getElementById('feedbackDialog');
    if (!dialog || typeof dialog.showModal !== 'function') return;

    const body = dialog.querySelector('.modal-body');
    const formUrl = dialog.dataset.url;
    let opener = null;

    async function load(options = {}) {
        const response = await fetch(formUrl, {
            ...options,
            headers: { 'X-Requested-With': 'fetch' },
            credentials: 'same-origin',
        });
        if (!response.ok) throw new Error(`Сервер ответил ${response.status}`);
        return response.text();
    }

    function placeFocus() {
        const target = body.querySelector('[aria-invalid="true"]')
            || body.querySelector('.form-summary')
            || body.querySelector('.feedback-success-text')
            || body.querySelector('input:not([type="hidden"]), textarea');
        if (target) target.focus();
    }

    function showProblem(container, text) {
        let note = container.querySelector('.form-problem');
        if (!note) {
            note = document.createElement('p');
            note.className = 'form-summary form-problem';
            note.setAttribute('role', 'alert');
            container.prepend(note);
        }
        note.textContent = text;
    }

    async function openDialog(link) {
        opener = link;
        dialog.showModal();
        // Сохраняем уже загруженную форму, чтобы при повторном открытии не терялся черновик.
        if (body.querySelector('form')) {
            placeFocus();
            return;
        }
        body.innerHTML = '<p class="modal-loading">Загружаем форму…</p>';
        try {
            body.innerHTML = await load();
            placeFocus();
        } catch (error) {
            body.innerHTML = '';
            showProblem(body, 'Не получилось загрузить форму. Попробуйте ещё раз чуть позже.');
        }
    }

    document.querySelectorAll('[data-feedback-open]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            openDialog(link);
        });
    });

    // Обработчик вешаем на dialog, так как <form> перерисовывается после каждого ответа.
    dialog.addEventListener('submit', async (event) => {
        const form = event.target;
        event.preventDefault();

        const button = form.querySelector('[type="submit"]');
        button.disabled = true;
        button.textContent = 'Отправляем…';

        try {
            body.innerHTML = await load({ method: 'POST', body: new FormData(form) });
            placeFocus();
        } catch (error) {
            button.disabled = false;
            button.textContent = 'Отправить';
            showProblem(form, 'Не удалось отправить. Проверьте интернет и попробуйте ещё раз.');
        }
    });

    dialog.addEventListener('click', (event) => {
        if (event.target === dialog || event.target.closest('[data-dialog-close]')) {
            dialog.close();
        }
    });

    dialog.addEventListener('close', () => {
        if (body.querySelector('.feedback-success')) body.innerHTML = '';
        if (opener) opener.focus();
    });
});
