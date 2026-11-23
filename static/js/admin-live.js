/* Периодический опрос счётчика непрочитанных сообщений и обновление сводки админки. */
(function () {
    const POLL_INTERVAL = 20 * 1000;

    // Классы совпадают с unfold/helpers/badge.html для визуальной согласованности.
    const BADGE_CLASSES = 'sidebar-badge font-semibold h-[18px] leading-[18px] ms-2 px-1 relative '
        + 'rounded-xs text-center text-[11px] whitespace-nowrap uppercase min-w-[18px] '
        + 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400';

    let menuLink = null;
    let latestId = null;
    let lastUnread = null;
    let toast = null;

    // Вызывается также из admin-messages.js и admin-list-toolbar.js.
    window.updateUnreadCount = function (count) {
        lastUnread = count;
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
            toast.setAttribute('role', 'status');
            document.body.append(toast);
        }
        toast.innerHTML = `
            <span class="material-symbols-outlined" aria-hidden="true">mark_email_unread</span>
            <span class="live-toast-text"></span>
            <a class="live-toast-link" href="${menuLink.getAttribute('href')}">Открыть</a>
            <button type="button" class="live-toast-close" aria-label="Скрыть уведомление">
                <span class="material-symbols-outlined" aria-hidden="true">close</span>
            </button>`;
        // Данные посетителя вставляем только через textContent во избежание XSS.
        toast.querySelector('.live-toast-text').textContent = `Новое сообщение от ${email}`;
        toast.querySelector('.live-toast-close').addEventListener('click', () => {
            toast.hidden = true;
        });
        toast.hidden = false;
    }

    async function refreshLatestMessages() {
        const box = document.querySelector('[data-latest-messages]');
        if (!box) return;
        const response = await fetch(box.dataset.url, { credentials: 'same-origin' });
        if (response.ok) box.innerHTML = await response.text();
    }

    async function check() {
        try {
            const response = await fetch(menuLink.dataset.statusUrl, { credentials: 'same-origin' });
            if (!response.ok) return;
            const data = await response.json();

            const isFirstCheck = latestId === null;
            const hasNewMessage = !isFirstCheck && data.latest_id > latestId;
            const unreadChanged = !isFirstCheck && data.unread !== lastUnread;

            window.updateUnreadCount(data.unread);
            if (hasNewMessage) showToast(data.latest_email);
            if (hasNewMessage || unreadChanged) await refreshLatestMessages();
            latestId = data.latest_id;
        } catch (error) {
            // Сетевые сбои игнорируем: опрос повторится на следующем интервале.
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        menuLink = document.querySelector('[data-status-url]');
        if (!menuLink) return;

        check();
        setInterval(() => {
            if (document.visibilityState === 'visible') check();
        }, POLL_INTERVAL);
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') check();
        });
    });
})();
