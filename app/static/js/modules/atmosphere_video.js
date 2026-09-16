/** Atmosphere enhancement: poster first, playback only when appropriate and visible. */
export function initAtmosphereVideo() {
    const video = document.querySelector('[data-video-src]');
    const button = document.querySelector('.media-toggle');
    if (!video || !button || !window.matchMedia) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const connection = navigator.connection;
    let visible = true, pausedByUser = false, failed = false, destroyed = false;
    const constrained = () => reduced.matches || connection?.saveData || ['slow-2g', '2g'].includes(connection?.effectiveType);
    const update = () => {
        const playing = !video.paused && !failed;
        video.classList.toggle('is-playing', playing);
        button.textContent = playing ? 'Pausar vídeo' : 'Reproducir vídeo';
        button.setAttribute('aria-pressed', String(playing));
    };
    async function play(explicit = false) {
        if (failed || destroyed || document.hidden || !visible || (!explicit && (constrained() || pausedByUser))) return;
        if (!video.getAttribute('src')) video.src = video.dataset.videoSrc;
        try {
            video.muted = true;
            await video.play();
            if (destroyed || document.hidden || !visible || pausedByUser) video.pause();
        } catch { /* A browser may disallow autoplay; the existing poster remains. */ }
        update();
    }
    button.addEventListener('click', () => {
        if (video.paused) { pausedByUser = false; play(true); }
        else { pausedByUser = true; video.pause(); update(); }
    });
    video.addEventListener('playing', update);
    video.addEventListener('pause', update);
    video.addEventListener('error', () => { failed = true; video.pause(); video.classList.remove('is-playing'); button.hidden = true; });
    const configure = () => {
        if (constrained() || document.hidden) { video.pause(); update(); }
        else play();
    };
    reduced.addEventListener('change', configure);
    connection?.addEventListener?.('change', configure);
    document.addEventListener('visibilitychange', configure);
    if (window.IntersectionObserver) {
        const observer = new IntersectionObserver(entries => {
            visible = entries[0].isIntersecting;
            if (visible) play(); else { video.pause(); update(); }
        }, { threshold: .1 });
        observer.observe(video);
        window.addEventListener('pagehide', () => observer.disconnect(), { once: true });
        window.addEventListener('pageshow', event => { if (event.persisted) { destroyed = false; observer.observe(video); configure(); } });
    } else play();
    window.addEventListener('pagehide', () => { destroyed = true; video.pause(); });
    update();
}
