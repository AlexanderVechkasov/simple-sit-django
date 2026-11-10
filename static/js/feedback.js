/*
 * Окно «Написать нам».
 *
 * Без JS ссылка в шапке просто ведёт на страницу /feedback/.
 * С JS форма открывается в окне поверх текущей страницы и отправляется
 * без перезагрузки (через fetch). Проверяет и сохраняет её всё тот же
 * Django — JS только приносит и уносит кусочки HTML.
 */
document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.getElementById('feedbackDialog');
    // Нет окна или браузер не знает <dialog> — пусть работает обычная ссылка.
    if (!dialog || typeof dialog.showModal !== 'function') return;

    const body = dialog.querySelector('.modal-body');
    const formUrl = dialog.dataset.url;
    let opener = null; // откуда открыли — туда вернём фокус

    // Запрос к Django с пометкой «я из окна»: в ответ придёт только кусок HTML.
    async function load(options = {}) {
        const response = await fetch(formUrl, {
            ...options,
            headers: { 'X-Requested-With': 'fetch' },
            credentials: 'same-origin',
        });
        if (!response.ok) throw new Error(`Сервер ответил ${response.status}`);
        return response.text();
    }

    // После загрузки ставим фокус туда, где он нужен человеку:
    // на первое поле с ошибкой, на общее сообщение об ошибке,
    // на «Спасибо» или на первое поле формы.
    function placeFocus() {
        const target = body.querySelector('[aria-invalid="true"]')
            || body.querySelector('.form-summary')
            || body.querySelector('.feedback-success-text')
            || body.querySelector('input:not([type="hidden"]), textarea');
        if (target) target.focus();
    }

    // Сообщение о сбое сети или сервера.
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
        // Форма уже загружена (например, человек закрыл окно и открыл снова) —
        // оставляем её: введённый текст не пропадёт.
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

    // Ссылки «Написать нам» открывают окно вместо перехода на страницу.
    document.querySelectorAll('[data-feedback-open]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            openDialog(link);
        });
    });

    // Отправка формы. Обработчик висит на окне, потому что сама форма
    // внутри заменяется после каждого ответа сервера.
    dialog.addEventListener('submit', async (event) => {
        const form = event.target;
        event.preventDefault();

        const button = form.querySelector('[type="submit"]');
        button.disabled = true; // защита от двойного нажатия
        button.textContent = 'Отправляем…';

        try {
            // FormData собирает все поля формы, включая скрытый csrf-токен.
            body.innerHTML = await load({ method: 'POST', body: new FormData(form) });
            placeFocus();
        } catch (error) {
            // Форму не трогаем, чтобы текст не пропал, — только сообщаем о сбое.
            button.disabled = false;
            button.textContent = 'Отправить';
            showProblem(form, 'Не удалось отправить. Проверьте интернет и попробуйте ещё раз.');
        }
    });

    // Закрытие: кнопки с data-dialog-close или клик по затемнённому фону.
    // Esc закрывает окно сам браузер.
    dialog.addEventListener('click', (event) => {
        if (event.target === dialog || event.target.closest('[data-dialog-close]')) {
            dialog.close();
        }
    });

    dialog.addEventListener('close', () => {
        // После «Спасибо» в следующий раз загрузим чистую форму.
        if (body.querySelector('.feedback-success')) body.innerHTML = '';
        if (opener) opener.focus();
    });
});
