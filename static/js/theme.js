/*
 * Тема оформления: светлая или тёмная.
 *
 * Файл подключён в <head> БЕЗ defer: тема должна примениться до того,
 * как браузер нарисует страницу, иначе на мгновение мелькнёт не та тема.
 *
 * Пока пользователь ничего не выбрал, тема берётся из настроек системы.
 * Выбор кнопкой запоминается в браузере (localStorage).
 */
(function () {
    const STORAGE_KEY = 'theme';
    const root = document.documentElement; // элемент <html>
    const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');

    function readSaved() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch (error) {
            return null; // хранилище недоступно (например, приватный режим)
        }
    }

    // 1. Сразу применяем сохранённый выбор, если он был.
    const saved = readSaved();
    if (saved === 'light' || saved === 'dark') {
        root.dataset.theme = saved; // станет <html data-theme="dark">
    }

    // 2. Когда страница построена — оживляем кнопку в шапке.
    document.addEventListener('DOMContentLoaded', () => {
        const button = document.querySelector('.theme-toggle');
        if (!button) return;

        function isDark() {
            if (root.dataset.theme) return root.dataset.theme === 'dark';
            return darkQuery.matches;
        }

        function updateButton() {
            // aria-pressed="true" — скринридер скажет «Тёмная тема, нажата»
            button.setAttribute('aria-pressed', String(isDark()));
        }

        button.hidden = false; // без JS кнопка не нужна — работает тема системы
        updateButton();

        button.addEventListener('click', () => {
            const next = isDark() ? 'light' : 'dark';
            root.dataset.theme = next;
            try {
                localStorage.setItem(STORAGE_KEY, next);
                localStorage.setItem('adminTheme', JSON.stringify(next));
            } catch (error) {
                // не запомнили — не страшно, тема всё равно переключилась
            }
            updateButton();
        });

        // Пользователь сменил тему в настройках системы, пока сайт открыт.
        darkQuery.addEventListener('change', updateButton);
    });
})();
