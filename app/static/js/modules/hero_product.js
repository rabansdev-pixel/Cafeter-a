/**
 * Módulo: HeroProduct
 * Provee interacción de inclinación 3D y paralaje suave con el cursor del mouse.
 */
export function initHeroProduct() {
    const stage = document.querySelector('.hero-product-stage');
    const coffeeBag = document.querySelector('.hero-coffee-bag');
    const backdrop = document.querySelector('.hero-visual-backdrop');

    if (!stage || !coffeeBag) return;

    let bounds = stage.getBoundingClientRect();

    window.addEventListener('resize', () => {
        bounds = stage.getBoundingClientRect();
    });

    stage.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX - bounds.left;
        const mouseY = e.clientY - bounds.top;

        const xPct = (mouseX / bounds.width - 0.5) * 2; // -1 to 1
        const yPct = (mouseY / bounds.height - 0.5) * 2; // -1 to 1

        const tiltX = -yPct * 12; // deg
        const tiltY = xPct * 15;  // deg

        coffeeBag.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateY(-8px) scale(1.03)`;
        
        if (backdrop) {
            backdrop.style.transform = `translate(${xPct * 18}px, ${yPct * 18}px)`;
        }
    });

    stage.addEventListener('mouseleave', () => {
        coffeeBag.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0) scale(1)';
        if (backdrop) {
            backdrop.style.transform = 'translate(0px, 0px)';
        }
    });
}
