import { initProductScene } from './modules/product_scene.js';
import { initHeroProduct } from './modules/hero_product.js';
import { initTastingRadar } from './modules/tasting_radar.js';
import { initCartDrawer } from './modules/cart_drawer.js';
import { initHomeAnimations } from './modules/home_animations.js';
import { initNavigation } from './modules/navigation.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log('☕ ZERO-DAY COFFEE iniciada');

    // Inicializar micro-interacciones y módulos
    initHeroProduct();
    initTastingRadar();
    initCartDrawer();
    initNavigation();
    initHomeAnimations();
    initProductScene();
});
