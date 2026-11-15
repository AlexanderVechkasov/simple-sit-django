/*
 * Одна тема на сайт и админку.
 *
 * Сайт хранит выбор в localStorage под ключом "theme": "light" или "dark"
 * (нет ключа — тема как в системе). Unfold хранит свой выбор под ключом
 * "adminTheme": "light", "dark" или "auto" (в формате JSON, с кавычками).
 *
 * Когда уходим со страницы админки (переход на сайт, другая вкладка,
 * закрытие), переписываем выбор админки в ключ сайта. Обратную сторону
 * делает static/js/theme.js: кнопка на сайте пишет в оба ключа.
 *
 * Подключается на всех страницах админки (и на странице входа) через UNFOLD["SCRIPTS"].
 */
(function () {
    function copyAdminThemeToSite() {
        try {
            const adminTheme = JSON.parse(localStorage.getItem('adminTheme'));
            if (adminTheme === 'light' || adminTheme === 'dark') {
                localStorage.setItem('theme', adminTheme);
            } else if (adminTheme === 'auto') {
                localStorage.removeItem('theme'); // сайт тоже возьмёт тему системы
            }
        } catch (error) {
            // хранилище недоступно или там что-то странное — просто ничего не делаем
        }
    }

    // pagehide — уходим со страницы; visibilitychange — переключились на другую вкладку.
    window.addEventListener('pagehide', copyAdminThemeToSite);
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') copyAdminThemeToSite();
    });
})();
