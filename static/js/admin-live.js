/*
 * «Живая» админка: раз в 20 секунд спрашиваем сервер, сколько непрочитанных
 * сообщений и не пришло ли новое. Обновляем число в меню и на «Сводке»,
 * а о новом сообщении показываем уведомление — без перезагрузки страницы.
 *
 * Подключается на всех страницах админки через UNFOLD["SCRIPTS"].
 */
(function () {
    const POLL_INTERVAL = 20 * 1000; // 20 секунд

    // Классы значка — те же, что у Unfold (шаблон unfold/helpers/badge.html)
    const BADGE_CLASSES = 'sidebar-badge font-semibold h-[18px] leading-[18px] ms-2 px-1 relative '
        + 'rounded-xs text-center text-[11px] whitespace-nowrap uppercase min-w-[18px] '
        + 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400';

    let menuLink = null;   // ссылка «Сообщения» в боковом меню
    let latestId = null;   // номер самого нового сообщения, которое мы уже видели
    let toast = null;

    // Обновить число непрочитанных в меню и на «Сводке».
    // Функция доступна и другим скриптам (её вызывает admin-messages.js).
    window.updateUnreadCount = function (count) {
        if (menuLink) {
            let badge = menuLink.querySelector('.sidebar-badge');
            if (count > 0) {
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = BADGE_CLASSES;
                    menuLink.append(badge);
                }
                badge.textContent = count;
            } else if (badge) {
                badge.remove();
            }
        }
        document.querySelectorAll('[data-unread-count]').forEach((element) => {
            element.textContent = count;
        });
    };

    function showToast(email) {
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'live-toast';
            toast.setAttribute('role', 'status'); // скринридер прочитает сам
            document.body.append(toast);
        }
        toast.innerHTML = `
            <span class="material-symbols-outlined" aria-hidden="true">mark_email_unread</span>
            <span class="live-toast-text"></span>
            <a class="live-toast-link" href="${menuLink.getAttribute('href')}">Открыть</a>
            <button type="button" class="live-toast-close" aria-label="Скрыть уведомление">
                <span class="material-symbols-outlined" aria-hidden="true">close</span>
            </button>`;
        // Почту вставляем через textContent — это данные посетителя.
        toast.querySelector('.live-toast-text').textContent = `Новое сообщение от ${email}`;
        toast.querySelector('.live-toast-close').addEventListener('click', () => {
            toast.hidden = true;
        });
        toast.hidden = false;
    }

    async function check() {
        try {
            const response = await fetch(menuLink.dataset.statusUrl, { credentials: 'same-origin' });
            if (!response.ok) return;
            const data = await response.json();
            window.updateUnreadCount(data.unread);
            if (latestId !== null && data.latest_id > latestId) {
                showToast(data.latest_email);
            }
            latestId = data.latest_id;
        } catch (error) {
            // Нет сети — не страшно, попробуем в следующий раз.
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        menuLink = document.querySelector('[data-status-url]');
        if (!menuLink) return; // страница входа или нет прав на сообщения

        check(); // сразу запоминаем, какое сообщение сейчас самое новое
        setInterval(() => {
            // Вкладка в фоне — не дёргаем сервер зря.
            if (document.visibilityState === 'visible') check();
        }, POLL_INTERVAL);
        // Вернулись на вкладку — проверяем сразу.
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') check();
        });
    });
})();
