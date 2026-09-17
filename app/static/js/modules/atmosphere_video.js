/** Atmosphere enhancement: poster first, playback only when appropriate and visible. */
export function initAtmosphereVideo() {
    document.querySelectorAll('video').forEach(initVideo);
}

function initVideo(video) {
    const button = video.closest('[data-video-container]')?.querySelector('.media-toggle');
    if (!video || !window.matchMedia) return;
    video.muted = true;
    video.defaultMuted = true;
    video.loop = true;
    video.playsInline = true;
    video.autoplay = false; // Visibility and motion preferences control playback below.
    video.controls = false;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const connection = navigator.connection;
    let visible = true, pausedByUser = false, failed = false, destroyed = false;
    const constrained = () => reduced.matches || connection?.saveData || ['slow-2g', '2g'].includes(connection?.effectiveType);
    const update = () => {
        const playing = !video.paused && !failed;
        video.classList.toggle('is-playing', playing);
        if (button) {
            button.textContent = playing ? 'Pausar vídeo' : 'Reproducir vídeo';
            button.setAttribute('aria-pressed', String(playing));
        }
    };
    async function play(explicit = false) {
        if (failed || destroyed || document.hidden || !visible || (!explicit && (constrained() || pausedByUser))) return;
        if (!video.getAttribute('src')) {
            // Select once before loading: never fetch both desktop and mobile files.
            const source = [...video.querySelectorAll('source[data-src]')].find(candidate =>
                (!candidate.media || window.matchMedia(candidate.media).matches) &&
                video.canPlayType(candidate.type)
            );
            const src = source?.dataset.src || video.dataset.videoSrc;
            if (src) video.src = src;
        }
        try {
            video.muted = true;
            await video.play();
            if (destroyed || document.hidden || !visible || pausedByUser) video.pause();
        } catch { /* A browser may disallow autoplay; the existing poster remains. */ }
        update();
    }
    button?.addEventListener('click', () => {
        if (video.paused) { pausedByUser = false; play(true); }
        else { pausedByUser = true; video.pause(); update(); }
    });
    video.addEventListener('playing', update);
    video.addEventListener('pause', update);
    video.addEventListener('error', () => { failed = true; video.pause(); video.classList.remove('is-playing'); if (button) button.hidden = true; });
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
