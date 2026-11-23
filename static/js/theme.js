/*
 * Переключение темы оформления.
 * Подключается в <head> без defer, чтобы применить data-theme до первого рендера (без FOUC).
 */
(function () {
    const STORAGE_KEY = 'theme';
    const root = document.documentElement;
    const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');

    function readSaved() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch (error) {
            return null;
        }
    }

    const saved = readSaved();
    if (saved === 'light' || saved === 'dark') {
        root.dataset.theme = saved;
    }

    document.addEventListener('DOMContentLoaded', () => {
        const button = document.querySelector('.theme-toggle');
        if (!button) return;

        function isDark() {
            if (root.dataset.theme) return root.dataset.theme === 'dark';
            return darkQuery.matches;
        }

        function updateButton() {
            button.setAttribute('aria-pressed', String(isDark()));
        }

        button.hidden = false;
        updateButton();

        button.addEventListener('click', () => {
            const next = isDark() ? 'light' : 'dark';
            root.dataset.theme = next;
            try {
                localStorage.setItem(STORAGE_KEY, next);
                // Дублируем в ключ Unfold для синхронизации темы с админкой.
                localStorage.setItem('adminTheme', JSON.stringify(next));
            } catch (error) {
                // Игнорируем недоступность localStorage (например, в приватном режиме).
            }
            updateButton();
        });

        darkQuery.addEventListener('change', updateButton);
    });
})();
