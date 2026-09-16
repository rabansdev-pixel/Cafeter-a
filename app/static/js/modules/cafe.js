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
