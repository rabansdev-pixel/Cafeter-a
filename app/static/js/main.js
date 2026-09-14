import { initHeroProduct } from './modules/hero_product.js';
import { initTastingRadar } from './modules/tasting_radar.js';
import { initCartDrawer } from './modules/cart_drawer.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log('☕ Cafetería de Especialidad Atelier iniciada');

    // Inicializar micro-interacciones y módulos
    initHeroProduct();
    initTastingRadar();
    initCartDrawer();
});
