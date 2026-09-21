/** Native scroll, progressive enhancement and a single scheduled frame. */
let disposeHome;

export function initHomeAnimations() {
    disposeHome?.();
    const opening = document.querySelector('.opening');
    if (!opening || !window.matchMedia) return () => {};
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const desktop = window.matchMedia('(min-width: 1024px) and (min-height: 650px)');
    const word = opening.querySelector('.opening-word');
    const product = opening.querySelector('.opening-product');
    const story = document.querySelector('.coffee-story');
    const chapters = [...document.querySelectorAll('.story-chapter')];
    const reveals = [...document.querySelectorAll('[data-reveal]')];
    let observer;
    let frame = 0;
    let chapterIndex = -1;

    function render() {
        frame = 0;
        if (reduced.matches) return;
        const top = opening.getBoundingClientRect().top;
        const storyBounds = story?.getBoundingClientRect();
        if (desktop.matches) {
            const offset = Math.min(window.innerHeight, Math.max(0, -top));
            word.style.translate = `0 ${offset * .08}px`;
            if (product) product.style.translate = `0 ${-offset * .06}px`;
        }
        if (storyBounds && desktop.matches) {
            const distance = Math.max(1, storyBounds.height - window.innerHeight);
            const progress = Math.max(0, Math.min(1, -storyBounds.top / distance));
            story.style.setProperty('--story-progress', progress);
            const openingStory = story === opening;
            const brandStage = openingStory ? 1 : 0;
            const step = Math.floor(progress * (chapters.length + brandStage));
            const next = Math.min(chapters.length - 1, step - brandStage);
            if (openingStory) {
                story.style.setProperty('--brand-opacity', Math.max(0, 1 - progress * 7));
                story.style.setProperty('--details-opacity', next >= 0 ? 1 : 0);
                story.classList.toggle('has-story', next >= 0);
            }
            if (next !== chapterIndex) {
                chapters.forEach((chapter, index) => {
                    chapter.classList.toggle('is-current', index === next);
                    chapter.setAttribute('aria-hidden', String(index !== next));
                });
                chapterIndex = next;
            }
        }
    }

    function schedule() {
        if (!frame && !reduced.matches) frame = window.requestAnimationFrame(render);
    }

    function configure() {
        observer?.disconnect();
        window.cancelAnimationFrame(frame);
        frame = 0;
        chapterIndex = -2;
        story?.classList.remove('has-story');
        story?.style.removeProperty('--brand-opacity');
        story?.style.removeProperty('--details-opacity');
        word.style.removeProperty('translate');
        product?.style.removeProperty('translate');
        story?.classList.toggle('is-pinned', desktop.matches && !reduced.matches);
        chapters.forEach(chapter => {
            chapter.classList.remove('is-current');
            chapter.removeAttribute('aria-hidden');
        });
        reveals.forEach(element => element.classList.remove('reveal-ready', 'is-revealed'));
        if (reduced.matches) return;
        if ('IntersectionObserver' in window) {
            observer = new window.IntersectionObserver(entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // Observe the unclipped parent, not the masked element.
                        reveals.filter(element => element.parentElement === entry.target)
                            .forEach(element => element.classList.add('is-revealed'));
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: .12 });
            reveals.forEach(element => {
                element.classList.add('reveal-ready');
                observer.observe(element.parentElement);
            });
        }
        schedule();
    }

    configure();
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule, { passive: true });
    reduced.addEventListener('change', configure);
    desktop.addEventListener('change', configure);
    disposeHome = () => {
        observer?.disconnect();
        window.cancelAnimationFrame(frame);
        window.removeEventListener('scroll', schedule);
        window.removeEventListener('resize', schedule);
        reduced.removeEventListener('change', configure);
        desktop.removeEventListener('change', configure);
        reveals.forEach(element => element.classList.remove('reveal-ready', 'is-revealed'));
        story?.classList.remove('is-pinned', 'has-story');
        story?.style.removeProperty('--brand-opacity');
        story?.style.removeProperty('--details-opacity');
        story?.style.removeProperty('--story-progress');
        chapters.forEach(chapter => chapter.removeAttribute('aria-hidden'));
        word.style.removeProperty('translate');
        product?.style.removeProperty('translate');
    };
    return disposeHome;
}
