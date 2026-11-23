/*
 * Синхронизация темы Unfold ("adminTheme" в JSON) с ключом сайта ("theme").
 * Обратная синхронизация выполняется в static/js/theme.js.
 */
(function () {
    function copyAdminThemeToSite() {
        try {
            const adminTheme = JSON.parse(localStorage.getItem('adminTheme'));
            if (adminTheme === 'light' || adminTheme === 'dark') {
                localStorage.setItem('theme', adminTheme);
            } else if (adminTheme === 'auto') {
                localStorage.removeItem('theme');
            }
        } catch (error) {
            // Игнорируем недоступность localStorage или повреждённый JSON.
        }
    }

    window.addEventListener('pagehide', copyAdminThemeToSite);
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') copyAdminThemeToSite();
    });
})();
