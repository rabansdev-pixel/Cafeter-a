import { initAtmosphereVideo } from './atmosphere_video.js';
/** Native scrolling, readable defaults and a keyboard-operable exhibition. */
export function initCafe() {
    const slides = [...document.querySelectorAll('.object-slide')];
    const controls = document.querySelector('.exhibition-controls');
    if (slides.length && controls) {
        let current = 0;
        const buttons = [...controls.querySelectorAll('[data-object-index]')];
        const show = index => {
            current = (index + slides.length) % slides.length;
            slides.forEach((slide, i) => { slide.hidden = i !== current; });
            buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === current)));
        };
        controls.hidden = false;
        buttons.forEach((button, i) => button.addEventListener('click', () => show(i)));
        controls.querySelector('.object-prev').addEventListener('click', () => show(current - 1));
        controls.querySelector('.object-next').addEventListener('click', () => show(current + 1));
        controls.addEventListener('keydown', event => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();
            show(event.key === 'Home' ? 0 : event.key === 'End' ? slides.length - 1 : current + (event.key === 'ArrowRight' ? 1 : -1));
            buttons[current].focus();
        });
        show(0);
    }
    if (!window.matchMedia) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    initAtmosphereVideo();
    if (document.body.classList.contains('zero-home')) {
        initHomeEditorialMotion();
        return;
    }
    if (!window.IntersectionObserver) return;
    const heading = document.querySelector('[data-words]');
    const words = [];
    if (heading) {
        const walker = document.createTreeWalker(heading, window.NodeFilter.SHOW_TEXT);
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        nodes.forEach(node => {
            const fragment = document.createDocumentFragment();
            node.textContent.split(/(\s+)/).forEach(text => {
                if (!text.trim()) fragment.append(document.createTextNode(text));
                else { const span = document.createElement('span'); span.className = 'word-reveal'; span.textContent = text; words.push(span); fragment.append(span); }
            });
            node.replaceWith(fragment);
        });
    }
    let frame = 0;
    const draw = () => {
        frame = 0;
        if (!heading) return;
        const rect = heading.getBoundingClientRect();
        const progress = reduced.matches ? 1 : Math.max(0, Math.min(1, (innerHeight * .92 - rect.top) / Math.max(1, innerHeight * .5)));
        words.forEach((word, i) => word.classList.toggle('read', i / words.length < progress));
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(draw); };
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule, { passive: true });
    reduced.addEventListener('change', schedule);
    draw();
    if (!reduced.matches) {
        const observer = new IntersectionObserver(entries => entries.forEach(entry => {
            if (entry.isIntersecting) { entry.target.classList.remove('pending'); observer.unobserve(entry.target); }
        }), { threshold: .1 });
        document.querySelectorAll('[data-cafe-reveal]').forEach(element => { element.classList.add('cafe-reveal', 'pending'); observer.observe(element); });
        window.addEventListener('pagehide', () => observer.disconnect(), { once: true });
    }
    window.addEventListener('pagehide', () => {
        window.removeEventListener('scroll', schedule); window.removeEventListener('resize', schedule);
        reduced.removeEventListener('change', schedule); cancelAnimationFrame(frame);
    }, { once: true });
}


/** Homepage word entrances and a scroll-linked reading reveal; no scroll interception. */
function initHomeEditorialMotion() {
    if (!window.IntersectionObserver) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const headings = [...document.querySelectorAll('[data-home-pull]')];
    const cards = [...document.querySelectorAll('[data-home-card]')];
    const paragraph = document.querySelector('[data-home-letters]');
    const letters = [];
    let observer, frame = 0, paragraphVisible = false, prepared = false;
    function accessibleCopy(element) {
        const copy = document.createElement('span');
        copy.className = 'home-sr';
        copy.textContent = element.textContent.trim();
        return copy;
    }
    function prepare() {
        if (prepared) return;
        prepared = true;
        headings.forEach(heading => {
            const copy = accessibleCopy(heading);
            const walker = document.createTreeWalker(heading, window.NodeFilter.SHOW_TEXT);
            const nodes = [];
            while (walker.nextNode()) nodes.push(walker.currentNode);
            let wordIndex = 0;
            nodes.forEach(node => {
                const fragment = document.createDocumentFragment();
                node.textContent.split(/(\s+)/).forEach(word => {
                    if (!word.trim()) { fragment.append(document.createTextNode(word)); return; }
                    const mask = document.createElement('span');
                    mask.className = 'home-word-mask';
                    mask.setAttribute('aria-hidden', 'true');
                    const inner = document.createElement('span');
                    inner.textContent = word;
                    inner.style.setProperty('--word-delay', `${Math.min(wordIndex++ * .08, .48)}s`);
                    mask.append(inner); fragment.append(mask);
                });
                node.replaceWith(fragment);
            });
            heading.prepend(copy);
        });
        if (paragraph) {
            const copy = accessibleCopy(paragraph);
            const fragment = document.createDocumentFragment();
            // Keep whole words together, while giving each letter its own opacity.
            paragraph.textContent.split(/(\s+)/).forEach(word => {
                if (!word.trim()) { fragment.append(document.createTextNode(word)); return; }
                const group = document.createElement('span');
                group.style.whiteSpace = 'nowrap';
                group.setAttribute('aria-hidden', 'true');
                for (const letter of word) {
                    const span = document.createElement('span');
                    span.className = 'home-copy-letter'; span.textContent = letter;
                    letters.push(span); group.append(span);
                }
                fragment.append(group);
            });
            paragraph.replaceChildren(copy, fragment);
        }
    }
    function draw() {
        frame = 0;
        if (!paragraph || reduced.matches) return;
        const rect = paragraph.getBoundingClientRect();
        const progress = Math.max(0, Math.min(1, (window.innerHeight * .82 - rect.top) / Math.max(1, window.innerHeight * .6 + rect.height)));
        letters.forEach((letter, index) => {
            const start = index / letters.length - .1;
            const local = Math.max(0, Math.min(1, (progress - start) / .15));
            letter.style.setProperty('--letter-opacity', .25 + .75 * local);
        });
    }
    function schedule() {
        if (!frame && paragraphVisible && !reduced.matches) frame = window.requestAnimationFrame(draw);
    }
    function configure() {
        observer?.disconnect();
        window.cancelAnimationFrame(frame); frame = 0;
        if (reduced.matches) {
            [...headings, ...cards].forEach(node => node.classList.remove('home-ready', 'home-in-view'));
            letters.forEach(letter => letter.style.removeProperty('--letter-opacity'));
            return;
        }
        prepare();
        observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.target === paragraph) {
                    paragraphVisible = entry.isIntersecting;
                    schedule();
                } else if (entry.isIntersecting) {
                    entry.target.classList.add('home-in-view');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: .08 });
        headings.forEach(heading => { heading.classList.add('home-ready'); observer.observe(heading); });
        cards.forEach((card, index) => {
            card.style.setProperty('--card-delay', `${index * .12}s`);
            card.classList.add('home-ready'); observer.observe(card);
        });
        if (paragraph) { observer.observe(paragraph); draw(); }
    }
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule, { passive: true });
    reduced.addEventListener('change', configure);
    window.addEventListener('pagehide', () => { observer?.disconnect(); window.cancelAnimationFrame(frame); frame = 0; });
    window.addEventListener('pageshow', event => { if (event.persisted) configure(); });
    configure();
}
