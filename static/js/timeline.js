/* Аккордеон карточек шкалы и полноэкранная галерея изображений на <dialog>. */
document.addEventListener('DOMContentLoaded', () => {
    setupTimeline();
    setupGallery();
});

function setupTimeline() {
    const timeline = document.querySelector('.timeline');
    if (!timeline) return;

    let openCard = null;

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
        if (openCard) setOpen(openCard, false);
        setOpen(card, true);
        openCard = card;
    }

    timeline.addEventListener('click', (event) => {
        const button = event.target.closest('.event-toggle');
        if (button) toggleCard(button.closest('.event'));
    });

    const target = document.getElementById(window.location.hash.slice(1));
    if (target && target.classList.contains('event')) {
        toggleCard(target);
        target.querySelector('.event-toggle').focus();
        // Снимаем якорь, чтобы при перезагрузке карточка не раскрывалась повторно.
        history.replaceState(null, '', window.location.pathname + window.location.search);
    }
}

function setupGallery() {
    const dialog = document.getElementById('imageGalleryModal');
    if (!dialog) return;

    const image = dialog.querySelector('#galleryImage');
    const caption = dialog.querySelector('.gallery-caption');
    const prevButton = dialog.querySelector('.gallery-prev');
    const nextButton = dialog.querySelector('.gallery-next');
    const closeButton = dialog.querySelector('.close-btn');

    let links = [];
    let index = 0;
    let opener = null;

    function show(newIndex) {
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
        const group = link.dataset.gallery;
        links = Array.from(document.querySelectorAll('a[data-gallery]'))
            .filter((item) => item.dataset.gallery === group);
        opener = link;
        const several = links.length > 1;
        prevButton.hidden = !several;
        nextButton.hidden = !several;
        show(links.indexOf(link));
        dialog.showModal();
    }

    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[data-gallery]');
        if (!link) return;
        event.preventDefault();
        open(link);
    });

    prevButton.addEventListener('click', () => show(index - 1));
    nextButton.addEventListener('click', () => show(index + 1));
    closeButton.addEventListener('click', () => dialog.close());

    dialog.addEventListener('keydown', (event) => {
        if (links.length < 2) return;
        if (event.key === 'ArrowLeft') show(index - 1);
        if (event.key === 'ArrowRight') show(index + 1);
    });

    dialog.addEventListener('click', (event) => {
        if (!event.target.closest('img, button, .gallery-caption')) dialog.close();
    });

    dialog.addEventListener('close', () => {
        image.removeAttribute('src');
        if (opener) opener.focus();
    });
}
