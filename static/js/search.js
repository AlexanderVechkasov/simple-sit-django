/* Модальный поиск событий через fetch с фолбэком на /search/. */
document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.getElementById('searchDialog');
    if (!dialog || typeof dialog.showModal !== 'function') return;

    const form = dialog.querySelector('.search-form');
    const input = dialog.querySelector('input[name="q"]');
    const resultsBox = dialog.querySelector('.search-results');
    const searchUrl = dialog.dataset.url;
    const DEBOUNCE_MS = 200;

    let opener = null;
    let timer = null;
    let controller = null;

    async function runSearch(query) {
        if (controller) controller.abort();
        const trimmed = query.trim();
        if (!trimmed) {
            resultsBox.innerHTML = '';
            return;
        }

        controller = new AbortController();
        const url = `${searchUrl}?q=${encodeURIComponent(trimmed)}`;
        try {
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'fetch' },
                credentials: 'same-origin',
                signal: controller.signal,
            });
            if (!response.ok) throw new Error(`Сервер ответил ${response.status}`);
            resultsBox.innerHTML = await response.text();
        } catch (error) {
            if (error.name === 'AbortError') return;
            resultsBox.innerHTML = '<p class="form-summary">Не удалось выполнить поиск. Попробуйте ещё раз.</p>';
        }
    }

    function openDialog(link) {
        opener = link;
        dialog.showModal();
        input.focus();
        input.select();
    }

    document.querySelectorAll('[data-search-open]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            openDialog(link);
        });
    });

    input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(() => runSearch(input.value), DEBOUNCE_MS);
    });

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        clearTimeout(timer);
        runSearch(input.value);
    });

    dialog.addEventListener('click', (event) => {
        if (event.target === dialog || event.target.closest('[data-dialog-close]')) {
            dialog.close();
        }
    });

    dialog.addEventListener('close', () => {
        clearTimeout(timer);
        if (controller) controller.abort();
        if (opener) opener.focus();
    });
});
