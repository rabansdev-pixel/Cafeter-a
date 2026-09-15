/** Optional product photography in WebGL. Static image remains the source of truth. */
let disposeCurrent;
export function initProductScene(loadScene = () => import('./product_scene_renderer.js')) {
    disposeCurrent?.();
    const host = document.querySelector('.opening-product[data-model]');
    if (!host || !window.matchMedia || !window.IntersectionObserver) return () => {};
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const desktop = window.matchMedia('(min-width: 1024px)');
    const connection = window.navigator.connection;
    let scene, pending = false, failed = false, disposed = false, visible = false, frame = 0;
    let generation = 0;
    let controller;
    const eligible = () => desktop.matches && !reduced.matches && !connection?.saveData
        && !['slow-2g', '2g', '3g'].includes(connection?.effectiveType)
        && (window.navigator.deviceMemory || 8) >= 4
        && (window.navigator.hardwareConcurrency || 4) >= 4;
    function reset() {
        generation++;
        controller?.abort();
        pending = false;
        window.cancelAnimationFrame(frame);
        frame = 0;
        host.classList.remove('model-ready');
        scene?.dispose();
        scene = undefined;
    }
    function render() {
        frame = 0;
        if (!scene || !visible || document.hidden || !eligible()) return;
        const bounds = host.closest('.opening').getBoundingClientRect();
        const progress = Math.max(0, Math.min(1, -bounds.top / Math.max(1, bounds.height - window.innerHeight)));
        scene.render(progress);
    }
    function schedule() {
        if (!frame && scene && visible && !document.hidden) frame = window.requestAnimationFrame(render);
    }
    async function activate() {
        if (disposed || !eligible()) { reset(); return; }
        if (scene) { schedule(); return; }
        if (!visible || pending || failed) return;
        pending = true;
        const ticket = ++generation;
        controller = new AbortController();
        const signal = controller.signal;
        try {
            const module = await loadScene();
            if (disposed || ticket !== generation) return;
            const loaded = await module.createProductScene(host, signal);
            if (disposed || ticket !== generation || !eligible()) { loaded.dispose(); return; }
            scene = loaded;
            render();
            host.classList.add('model-ready');
        } catch {
            // Model, context or network failure must never affect shopping.
            if (ticket === generation) { failed = true; reset(); }
        } finally {
            if (ticket === generation) pending = false;
        }
    }
    const observer = new window.IntersectionObserver(entries => {
        visible = entries.some(entry => entry.isIntersecting);
        if (visible) activate();
        else { window.cancelAnimationFrame(frame); frame = 0; }
    });
    observer.observe(host);
    const contextLost = event => { event.preventDefault(); failed = true; reset(); };
    host.addEventListener('webglcontextlost', contextLost, true);
    reduced.addEventListener('change', activate);
    desktop.addEventListener('change', activate);
    connection?.addEventListener('change', activate);
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule, { passive: true });
    document.addEventListener('visibilitychange', schedule);
    disposeCurrent = () => {
        if (disposed) return;
        disposed = true;
        observer.disconnect();
        reset();
        host.removeEventListener('webglcontextlost', contextLost, true);
        reduced.removeEventListener('change', activate);
        desktop.removeEventListener('change', activate);
        connection?.removeEventListener('change', activate);
        window.removeEventListener('scroll', schedule);
        window.removeEventListener('resize', schedule);
        document.removeEventListener('visibilitychange', schedule);
    };
    return disposeCurrent;
}
