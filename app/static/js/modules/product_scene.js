/** One shared WebGL canvas, transferred between visible editorial scenes. */
let disposeCurrent;
export function initProductScene(loadScene = () => import('./product_scene_renderer.js')) {
    disposeCurrent?.();
    const hosts = [...document.querySelectorAll('[data-model]')];
    if (!hosts.length || !window.matchMedia || !window.IntersectionObserver) return () => {};
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const connection = window.navigator.connection;
    const visible = new Map();
    const failed = new Set();
    let scene, active, controller, module, disposed = false, generation = 0, frame = 0;
    const eligible = () => !reduced.matches && !connection?.saveData
        && !['slow-2g', '2g'].includes(connection?.effectiveType)
        && (window.navigator.deviceMemory || 8) >= 2;
    function reset() {
        generation++;
        controller?.abort();
        window.cancelAnimationFrame(frame); frame = 0;
        active?.classList.remove('model-ready');
        scene?.dispose(); scene = undefined; active = undefined;
    }
    function render() {
        frame = 0;
        if (!scene || !active || document.hidden || !eligible()) return;
        const rect = active.getBoundingClientRect();
        scene.render(Math.max(0, Math.min(1, (window.innerHeight - rect.top) / (window.innerHeight + rect.height))));
    }
    function schedule() {
        if (!frame && scene && !document.hidden) frame = window.requestAnimationFrame(render);
    }
    async function activate(preferred) {
        if (disposed) return;
        if (!eligible() || document.hidden) { reset(); return; }
        const choices = [...visible].filter(([host, ratio]) => ratio > .1 && !failed.has(host));
        choices.sort((a, b) => b[1] - a[1]);
        const selected = hosts.includes(preferred) && (visible.get(preferred) || 0) > .1;
        const next = selected ? preferred : active && (visible.get(active) || 0) > .3 ? active : choices[0]?.[0];
        if (next === active) { schedule(); return; }
        reset();
        if (!next) return;
        active = next;
        const ticket = generation;
        controller = new AbortController();
        const signal = controller.signal;
        try {
            module ||= await loadScene();
            if (disposed || ticket !== generation) return;
            const loaded = await module.createProductScene(next, signal);
            if (disposed || ticket !== generation) { loaded.dispose(); return; }
            scene = loaded;
            scene.render(.5);
            next.classList.add('model-ready');
        } catch {
            if (ticket === generation) {
                failed.add(next); reset();
            }
        }
    }
    const observer = new window.IntersectionObserver(entries => {
        entries.forEach(entry => visible.set(entry.target, entry.isIntersecting ? entry.intersectionRatio : 0));
        activate();
    }, { threshold: [0, .1, .3, .6, 1] });
    const intents = hosts.map(host => {
        observer.observe(host);
        const choose = () => activate(host);
        host.addEventListener('pointerenter', choose);
        host.closest('a')?.addEventListener('focus', choose);
        return { host, choose };
    });
    const contextLost = event => {
        event.preventDefault();
        if (active) failed.add(active);
        reset(); module?.disposeRenderer?.();
    };
    hosts.forEach(host => host.addEventListener('webglcontextlost', contextLost, true));
    reduced.addEventListener('change', activate);
    connection?.addEventListener?.('change', activate);
    document.addEventListener('visibilitychange', activate);
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule, { passive: true });
    disposeCurrent = () => {
        if (disposed) return;
        disposed = true; observer.disconnect(); reset(); module?.disposeRenderer?.();
        intents.forEach(({ host, choose }) => {
            host.removeEventListener('pointerenter', choose);
            host.closest('a')?.removeEventListener('focus', choose);
        });
        hosts.forEach(host => host.removeEventListener('webglcontextlost', contextLost, true));
        reduced.removeEventListener('change', activate);
        connection?.removeEventListener?.('change', activate);
        document.removeEventListener('visibilitychange', activate);
        window.removeEventListener('scroll', schedule);
        window.removeEventListener('resize', schedule);
    };
    return disposeCurrent;
}
