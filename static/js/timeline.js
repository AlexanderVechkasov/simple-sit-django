/*
 * Интерактивность сайта:
 *  1) раскрытие карточек на шкале (одновременно открыта только одна);
 *  2) галерея изображений во всплывающем окне <dialog>.
 *
 * Без JS сайт тоже работает: статьи открываются по ссылкам,
 * а картинки — как обычные файлы.
 */
document.addEventListener('DOMContentLoaded', () => {
    setupTimeline();
    setupGallery();
});

/* =====  Карточки на шкале ===== */

function setupTimeline() {
    const timeline = document.querySelector('.timeline');
    if (!timeline) return; // на странице статьи шкалы нет

    let openCard = null; // какая карточка сейчас раскрыта

    // Раскрыть (open = true) или свернуть (open = false) одну карточку.
    function setOpen(card, open) {
        const button = card.querySelector('.event-toggle');
        const body = document.getElementById(button.getAttribute('aria-controls'));
        button.setAttribute('aria-expanded', String(open));
        body.hidden = !open;
        card.classList.toggle('active', open);
    }

    function toggleCard(card) {
        if (card === openCard) {
            setOpen(card, false);
            openCard = null;
            return;
        }
        if (openCard) setOpen(openCard, false); // одновременно открыта только одна
        setOpen(card, true);
        openCard = card;
    }

    // Раскрывает и сворачивает только кнопка-заголовок: по тексту и
    // картинкам внутри раскрытой карточки можно кликать спокойно.
    timeline.addEventListener('click', (event) => {
        const button = event.target.closest('.event-toggle');
        if (button) toggleCard(button.closest('.event'));
    });

    // Пришли по ссылке «Вернуться на шкалу» (/#event-1914a) — раскрываем это событие.
    const target = document.getElementById(window.location.hash.slice(1));
    if (target && target.classList.contains('event')) {
        toggleCard(target);
        target.querySelector('.event-toggle').focus();
        // Убираем #event-… из адреса: якорь нужен только один раз,
        // иначе при обновлении страницы карточка раскроется снова.
        history.replaceState(null, '', window.location.pathname + window.location.search);
    }
}

/* ===== Галерея ===== */

function setupGallery() {
    const dialog = document.getElementById('imageGalleryModal');
    if (!dialog) return;

    const image = dialog.querySelector('#galleryImage');
    const caption = dialog.querySelector('.gallery-caption');
    const prevButton = dialog.querySelector('.gallery-prev');
    const nextButton = dialog.querySelector('.gallery-next');
    const closeButton = dialog.querySelector('.close-btn');

    let links = [];      // ссылки-картинки текущей группы
    let index = 0;       // какая из них показана
    let opener = null;   // откуда открыли — туда вернём фокус

    function show(newIndex) {
        // По кругу: после последней — первая, перед первой — последняя.
        index = (newIndex + links.length) % links.length;
        const link = links[index];
        const text = link.dataset.caption || '';
        image.src = link.href;
        image.alt = text;
        caption.textContent = links.length > 1
            ? `${text} (${index + 1} из ${links.length})`
            : text;
    }

    function open(link) {
        // Группа — все картинки с тем же data-gallery, в порядке на странице.
        const group = link.dataset.gallery;
        links = Array.from(document.querySelectorAll('a[data-gallery]'))
            .filter((item) => item.dataset.gallery === group);
        opener = link;
        const several = links.length > 1;
        prevButton.hidden = !several;
        nextButton.hidden = !several;
        show(links.indexOf(link));
        // showModal: окно поверх страницы, фон недоступен, Esc закрывает.
        dialog.showModal();
    }

    // Клик по картинке-ссылке открывает галерею вместо перехода на файл.
    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[data-gallery]');
        if (!link) return;
        event.preventDefault();
        open(link);
    });

    prevButton.addEventListener('click', () => show(index - 1));
    nextButton.addEventListener('click', () => show(index + 1));
    closeButton.addEventListener('click', () => dialog.close());

    // Стрелки ← → листают, если картинок несколько.
    dialog.addEventListener('keydown', (event) => {
        if (links.length < 2) return;
        if (event.key === 'ArrowLeft') show(index - 1);
        if (event.key === 'ArrowRight') show(index + 1);
    });

    // Клик по затемнённому фону (мимо содержимого) закрывает окно.
    dialog.addEventListener('click', (event) => {
        if (event.target === dialog) dialog.close();
    });

    // При любом закрытии (крестик, Esc, фон) возвращаем фокус на картинку.
    dialog.addEventListener('close', () => {
        image.removeAttribute('src');
        if (opener) opener.focus();
    });
}
